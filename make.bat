@ECHO off

if "%~1" == "" goto :help
if /I %1 == help goto :help
if /I %1 == lint goto :lint
if /I %1 == format goto :format
if /I %1 == test goto :test
if /I %1 == coverage goto :coverage
if /I %1 == build goto :build
goto :help

:help
echo.Please use `make ^<target^>` where ^<target^> is one of
echo.  lint         Check formatting issues
echo.  format       Fix formatting issues (where possible)
echo.  test         Run tests
echo.  coverage     Generate coverage report
echo.  build        Build python wheel package
goto :eof

:lint
ruff format . --check && ruff .
goto :eof

:format
ruff format . && ruff . --fix --show-fixes
goto :eof

:test
py.test
goto :eof

:coverage
coverage run -m pytest
coverage html
goto :eof

:build
rmdir /s /q .\build
rmdir /s /q .\dist
flit build
dir .\dist
goto :eof
