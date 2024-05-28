from shiny import reactive, req
from shiny.express import input, render, ui
from shiny import ui as core_ui
import rispy
from deduper.app.constants import DEDUPER_MAP, PAGE_SIZE, ANNOTATE_CHOICES
import pandas as pd
import io
import math

# TODO
# Choose RIS file - wording
# Add year to table
# Add selector for DB, link ID
# Select multiple of columns to show in table, default to year, title, abstract
# Bug: check radio box, turn annotate off, turn annotate back on; check didn't persist
#     annotations only save when page changes or download clicked?


annotations = reactive.value([])
page = reactive.value(1)

core_ui.card(
    core_ui.row(
        core_ui.column(6,ui.input_file("file","Choose file")),
        core_ui.column(6,ui.input_select("deduper_select","Choose deduper",{"id_and_title":"ID and title","id_only":"ID only","title_only":"Title only"}))
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
@reactive.event(results_slice,input["annotate"])
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
                id_div = ui.div(ui.div("ID",{"class":"fw-bold"}),data.get("id",""),{"class":"overflow-auto","style":"max-height:150px;"})
                title_div = ui.div(ui.div("Title",{"class":"fw-bold"}),data.get("title",""),{"class":"overflow-auto","style":"max-height:150px;"})
                abstract_div = ui.div(ui.div("Abstract",{"class":"fw-bold"}),ui.div(data.get("abstract",""),{"class":"overflow-auto","style":"max-height:150px;"}))
                row = core_ui.row(
                    core_ui.column(1,radio_button),
                    core_ui.column(3,id_div),
                    core_ui.column(3,title_div),
                    core_ui.column(5,abstract_div),
                    )
                rows.append(row)

        else:

            for data in result:
                id_div = ui.div(ui.div("ID",{"class":"fw-bold"}),data.get("id",""),{"class":"overflow-auto","style":"max-height:150px;"})
                title_div = ui.div(ui.div("Title",{"class":"fw-bold"}),data.get("title",""),{"class":"overflow-auto","style":"max-height:150px;"})
                abstract_div = ui.div(ui.div("Abstract",{"class":"fw-bold"}),ui.div(data.get("abstract",""),{"class":"overflow-auto","style":"max-height:150px;"}))
                row = core_ui.row(
                    core_ui.column(3,id_div),
                    core_ui.column(3,title_div),
                    core_ui.column(6,abstract_div),
                    )
                rows.append(row)
        card = core_ui.card(*rows,id=id,class_="shiny-input-radiogroup")
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


ui.div(id="pagination_container")

@reactive.effect
def render_pagination():
    ui.remove_ui("#pagination_container *")
    components = []
    if page() > 1:
        components.extend(
            [
                ui.input_action_link(id="page_start",label="<<"),
                " ",
                ui.input_action_link(id="page_down",label="<"),
                " ",
            ]
        )
    components.append(f"Page {page()}")
    if page() < len(results())/PAGE_SIZE:
        components.extend(
            [
                " ",
                ui.input_action_link(id="page_up",label=">"),
                " ",
                ui.input_action_link(id="page_end",label=">>"),
            ]
        )

    ui.insert_ui(ui.div(*components),"#pagination_container")


@reactive.effect
@reactive.event(input["page_start"])
def page_start():
    page.set(1)

@reactive.effect
@reactive.event(input["page_down"])
def page_down():
    page.set(page()-1)

@reactive.effect
@reactive.event(input["page_up"])
def page_up():
    page.set(page()+1)

@reactive.effect
@reactive.event(input["page_end"])
def page_end():
    page.set(math.ceil(len(results())/PAGE_SIZE))













