from shiny import reactive, req
from shiny.express import input, render, ui
from shiny import ui as core_ui
import rispy
from deduper.app.constants import DEDUPER_MAP, PAGE_SIZE, ANNOTATE_CHOICES
import pandas as pd
import io
import math
from deduper.app.icons import question_circle_fill

# TODO
# Select multiple of columns to show in table, default to id, title, abstract
# Add dynamic deduper creation (ie calculate columns after file upload, then have ui to select them and type of deduplication)
#     once this is done, add selector for ID column to work with ID links
# Bug: check radio box, turn annotate off, turn annotate back on; check didn't persist
#     annotations only save when page changes or download clicked?


annotations = reactive.value([])
page = reactive.value(1)

ID_URL_MAP ={
"---":None,
"PMID":"https://pubmed.ncbi.nlm.nih.gov/{id}/",
"WoS":"https://www.webofscience.com/wos/woscc/full-record/{id}",
"HERO":"https://heronet.epa.gov/heronet/index.cfm/reference/details/reference_id/{id}",
"DOI":"https://doi.org/{id}"}




core_ui.card(
    core_ui.row(
        core_ui.column(4,ui.input_file("file","Choose RIS file")),
        core_ui.column(4,ui.input_select("deduper_select",core_ui.tooltip(ui.span("Choose deduper ",question_circle_fill),"Deduplication will be done based on the chosen criteria (mixture of ID and title)",placement="right",id="deduper_select_tooltip"),{"id_and_title":"ID and title","id_only":"ID only","title_only":"Title only"})),
        core_ui.column(4,ui.input_select("id_url_select",core_ui.tooltip(ui.span("Show ID url ",question_circle_fill),"If a selection is made, the IDs shown in the computed table will link to their respective database URL.",placement="right",id="id_url_select_tooltip"),{k:k for k in ID_URL_MAP.keys()}))
        ),
    core_ui.card_footer(
        core_ui.row(
            core_ui.column(4,ui.input_action_button("compute", "Compute!")),
            core_ui.column(4,ui.div(id="download_container")),
            core_ui.column(4,ui.div(id="annotate_container")),
        )
    )
)

@reactive.calc
def records():
    file = req(input["file"]())
    with open(file[0]["datapath"], 'r', errors="ignore") as f:
        return rispy.load(f)

@reactive.calc
def deduper():
    deduper_selection = req(input["deduper_select"]())
    return DEDUPER_MAP[deduper_selection]

@reactive.calc
@reactive.event(input["compute"])
def results():
    return deduper().get_duplicates(records())

@reactive.calc
def results_slice():
    start = (page()-1)*PAGE_SIZE
    end = page()*PAGE_SIZE
    return results()[start:end]

@reactive.calc
def annotations_slice():
    start = (page()-1)*PAGE_SIZE
    end = page()*PAGE_SIZE
    return annotations()[start:end]

@reactive.effect
def set_annotations():
    annotations.set([0]*len(records()))

ui.div(id="pagination_container_0")

ui.div(id="results_container")

def download_results():
    req(records())    
    results = deduper().get_duplicates(records())
    export = [{"duplicate_group":i, "id":record["id"]} for i,group in enumerate(results) for record in group]
    with io.BytesIO() as buf:
        pd.DataFrame(export).to_excel(buf,index=False)
        yield buf.getvalue()

def download_annotated_results():
    req(records())    
    results = deduper().get_duplicates(records())
    export = [{"duplicate_group":i, "id":record["id"], "resolution":ANNOTATE_CHOICES.get(annotations()[i],"Duplicate identified"), "resolved_id":record["id"] if annotations()[i] < len(ANNOTATE_CHOICES) else group[annotations()[i]-len(ANNOTATE_CHOICES)]["id"]} for i,group in enumerate(results) for record in group]
    with io.BytesIO() as buf:
        pd.DataFrame(export).to_excel(buf,index=False)
        yield buf.getvalue()

@reactive.effect
@reactive.event(results)
def render_annotate():
    ui.remove_ui("#annotate_container *")
    ui.insert_ui(ui.input_checkbox(id="annotate", label="Annotate?"),"#annotate_container")

@reactive.effect
@reactive.event(input["annotate"])
def render_download():
    ui.remove_ui("#download_container *")
    download_func = download_annotated_results if input["annotate"]() else download_results
    ui.insert_ui(render.download(label="Download results", filename="duplicate_results.xlsx")(download_func),"#download_container")


@reactive.effect
@reactive.event(results_slice,input["annotate"],input["id_url_select"])
def render_results():
    ui.remove_ui("#results_container *")
    cards = []
    for x,result in enumerate(results_slice()):
        id = f"duplicate_{x}"
        rows = []
        selected = annotations_slice()[x]

        if input["annotate"]():
            for k,v in ANNOTATE_CHOICES.items():
                checked = {"checked":"checked"} if k == selected else {}
                radio_button = ui.tags.input(value=k,type="radio",name=id,**checked)
                row = core_ui.row(
                    core_ui.column(1,radio_button),
                    core_ui.column(11,ui.div(v,{"class":"fw-bold"})),
                    )
                rows.append(row)

            for y,data in enumerate(result,len(ANNOTATE_CHOICES)):
                checked = {"checked":"checked"} if y == selected else {}
                radio_button = ui.tags.input(value=y,type="radio",name=id,**checked)
                cols = [core_ui.column(1,radio_button)]
                for col_name in [("id","ID",1),("year","Year",1),("title","Title",3),("authors","Authors",2),("abstract","Abstract",4)]:
                    value = data.get(col_name[0],"")
                    if col_name[0] == "id" and (url:=ID_URL_MAP.get(input["id_url_select"]())) is not None:
                        value = ui.a(value,target="_blank",href=url.format(id=value))
                    col_contents = ui.div({"class":"overflow-auto","style":"max-height:150px;"},ui.div({"class":"fw-bold"},col_name[1]),value)
                    cols.append(ui.div({"class":f"col-sm-{col_name[2]}"},col_contents))
                row = core_ui.row(*cols)
                rows.append(row)

        else:

            for data in result:
                cols = []
                for col_name in [("id","ID",1),("year","Year",1),("title","Title",3),("authors","Authors",3),("abstract","Abstract",4)]:
                    value = data.get(col_name[0],"")
                    if col_name[0] == "id" and (url:=ID_URL_MAP.get(input["id_url_select"]())) is not None:
                        value = ui.a(value,target="_blank",href=url.format(id=value))
                    col_contents = ui.div({"class":"overflow-auto","style":"max-height:150px;"},ui.div({"class":"fw-bold"},col_name[1]),value)
                    cols.append(ui.div({"class":f"col-sm-{col_name[2]}"},col_contents))
                row = core_ui.row(*cols)
                rows.append(row)
        card = core_ui.card(ui.div({"class":"container"},*rows),id=id,class_="shiny-input-radiogroup")
        cards.append(card)
    if not cards:
        cards = [ui.p("No duplicates found!")]
    ui.insert_ui(ui.div(*cards),"#results_container")

@reactive.effect
@reactive.event(*[input[f"duplicate_{i}"] for i in range(PAGE_SIZE)])
def update_annotations():
    for x in range(len(results_slice())):
        y = (page()-1) * PAGE_SIZE + x
        annotations()[y] = int(input[f"duplicate_{x}"]())
    return


ui.div(id="pagination_container_1")

@reactive.effect
def render_pagination():
    ui.remove_ui("#pagination_container_0 *")
    ui.remove_ui("#pagination_container_1 *")
    def _render(id_suffix,*args):
        components = []
        if page() > 1:
            components.extend(
                [
                    ui.input_action_link(id=f"page_start_{id_suffix}",label="<<"),
                    " ",
                    ui.input_action_link(id=f"page_down_{id_suffix}",label="<"),
                    " ",
                ]
            )
        components.append(f"Page {page()}")
        if page() < len(results())/PAGE_SIZE:
            components.extend(
                [
                    " ",
                    ui.input_action_link(id=f"page_up_{id_suffix}",label=">"),
                    " ",
                    ui.input_action_link(id=f"page_end_{id_suffix}",label=">>"),
                ]
            )
        return ui.div(*components,*args)

    ui.insert_ui(_render(0,{"class":"mb-3"}),"#pagination_container_0")
    ui.insert_ui(_render(1),"#pagination_container_1")


@reactive.effect
@reactive.event(input["page_start_0"],input["page_start_1"])
def page_start():
    page.set(1)

@reactive.effect
@reactive.event(input["page_down_0"],input["page_down_1"])
def page_down():
    page.set(page()-1)

@reactive.effect
@reactive.event(input["page_up_0"],input["page_up_1"])
def page_up():
    page.set(page()+1)

@reactive.effect
@reactive.event(input["page_end_0"],input["page_end_1"])
def page_end():
    page.set(math.ceil(len(results())/PAGE_SIZE))













