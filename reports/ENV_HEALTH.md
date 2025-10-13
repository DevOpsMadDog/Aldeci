# Environment Health

Generated via tools/env/dependency_doctor.py.

## Detected Python Versions

- Python 3.10
- Python 3.11
- Python 3.12

> Constraints are compiled with the active interpreter because pip-tools no longer supports per-command python version overrides.

## Constraints for Python 3.10

```text
(no output)
```

## Constraints for Python 3.11

```text
(no output)
```

## Constraints for Python 3.12

```text
(no output)
```

## requirements.txt

```text
(no output)
```

## requirements-dev.txt

```text
(no output)
```

## Wheel Build

```text
Collecting annotated-types==0.7.0 (from -r /workspace/Aldeci/requirements.txt (line 7))
  Using cached annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting anyio==4.11.0 (from -r /workspace/Aldeci/requirements.txt (line 9))
  Using cached anyio-4.11.0-py3-none-any.whl.metadata (4.1 kB)
Collecting attrs==25.4.0 (from -r /workspace/Aldeci/requirements.txt (line 14))
  Using cached attrs-25.4.0-py3-none-any.whl.metadata (10 kB)
Collecting certifi==2025.10.5 (from -r /workspace/Aldeci/requirements.txt (line 18))
  Using cached certifi-2025.10.5-py3-none-any.whl.metadata (2.5 kB)
Collecting cffi==2.0.0 (from -r /workspace/Aldeci/requirements.txt (line 23))
  Using cached cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting charset-normalizer==3.4.3 (from -r /workspace/Aldeci/requirements.txt (line 25))
  Using cached charset_normalizer-3.4.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (36 kB)
Collecting click==8.3.0 (from -r /workspace/Aldeci/requirements.txt (line 27))
  Using cached click-8.3.0-py3-none-any.whl.metadata (2.6 kB)
Collecting colorama==0.4.6 (from -r /workspace/Aldeci/requirements.txt (line 31))
  Using cached colorama-0.4.6-py2.py3-none-any.whl.metadata (17 kB)
Collecting cryptography==46.0.2 (from -r /workspace/Aldeci/requirements.txt (line 33))
  Using cached cryptography-46.0.2-cp311-abi3-manylinux_2_34_x86_64.whl.metadata (5.7 kB)
Collecting defusedxml==0.7.1 (from -r /workspace/Aldeci/requirements.txt (line 35))
  Using cached defusedxml-0.7.1-py2.py3-none-any.whl.metadata (32 kB)
Collecting elementpath==5.0.4 (from -r /workspace/Aldeci/requirements.txt (line 37))
  Using cached elementpath-5.0.4-py3-none-any.whl.metadata (7.0 kB)
Collecting fastapi==0.119.0 (from -r /workspace/Aldeci/requirements.txt (line 39))
  Using cached fastapi-0.119.0-py3-none-any.whl.metadata (28 kB)
Collecting fastjsonschema==2.21.2 (from -r /workspace/Aldeci/requirements.txt (line 41))
  Using cached fastjsonschema-2.21.2-py3-none-any.whl.metadata (2.3 kB)
Collecting h11==0.16.0 (from -r /workspace/Aldeci/requirements.txt (line 43))
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting httpcore==1.0.9 (from -r /workspace/Aldeci/requirements.txt (line 47))
  Using cached httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting httptools==0.7.1 (from -r /workspace/Aldeci/requirements.txt (line 49))
  Using cached httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
Collecting httpx==0.28.1 (from -r /workspace/Aldeci/requirements.txt (line 51))
  Using cached httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting idna==3.11 (from -r /workspace/Aldeci/requirements.txt (line 53))
  Using cached idna-3.11-py3-none-any.whl.metadata (8.4 kB)
Collecting iniconfig==2.1.0 (from -r /workspace/Aldeci/requirements.txt (line 58))
  Using cached iniconfig-2.1.0-py3-none-any.whl.metadata (2.7 kB)
Collecting jsonschema==4.25.1 (from -r /workspace/Aldeci/requirements.txt (line 60))
  Using cached jsonschema-4.25.1-py3-none-any.whl.metadata (7.6 kB)
Collecting jsonschema-specifications==2025.9.1 (from -r /workspace/Aldeci/requirements.txt (line 62))
  Using cached jsonschema_specifications-2025.9.1-py3-none-any.whl.metadata (2.9 kB)
Collecting lib4sbom==0.8.8 (from -r /workspace/Aldeci/requirements.txt (line 64))
  Using cached lib4sbom-0.8.8-py2.py3-none-any.whl.metadata (45 kB)
Collecting mando==0.7.1 (from -r /workspace/Aldeci/requirements.txt (line 66))
  Using cached mando-0.7.1-py2.py3-none-any.whl.metadata (7.4 kB)
Collecting markdown-it-py==4.0.0 (from -r /workspace/Aldeci/requirements.txt (line 68))
  Using cached markdown_it_py-4.0.0-py3-none-any.whl.metadata (7.3 kB)
Collecting mdurl==0.1.2 (from -r /workspace/Aldeci/requirements.txt (line 70))
  Using cached mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting networkx==3.4.2 (from -r /workspace/Aldeci/requirements.txt (line 72))
  Using cached networkx-3.4.2-py3-none-any.whl.metadata (6.3 kB)
Collecting numpy==2.2.6 (from -r /workspace/Aldeci/requirements.txt (line 74))
  Using cached numpy-2.2.6-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (62 kB)
Collecting packaging==25.0 (from -r /workspace/Aldeci/requirements.txt (line 76))
  Using cached packaging-25.0-py3-none-any.whl.metadata (3.3 kB)
Collecting pluggy==1.6.0 (from -r /workspace/Aldeci/requirements.txt (line 78))
  Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
Collecting pycparser==2.23 (from -r /workspace/Aldeci/requirements.txt (line 80))
  Using cached pycparser-2.23-py3-none-any.whl.metadata (993 bytes)
Collecting pydantic==2.12.0 (from -r /workspace/Aldeci/requirements.txt (line 82))
  Using cached pydantic-2.12.0-py3-none-any.whl.metadata (83 kB)
Collecting pydantic-core==2.41.1 (from -r /workspace/Aldeci/requirements.txt (line 86))
  Using cached pydantic_core-2.41.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (7.3 kB)
Collecting pygments==2.19.2 (from -r /workspace/Aldeci/requirements.txt (line 88))
  Using cached pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
Collecting pytest==8.4.2 (from -r /workspace/Aldeci/requirements.txt (line 92))
  Using cached pytest-8.4.2-py3-none-any.whl.metadata (7.7 kB)
Collecting python-dotenv==1.1.1 (from -r /workspace/Aldeci/requirements.txt (line 94))
  Using cached python_dotenv-1.1.1-py3-none-any.whl.metadata (24 kB)
Collecting pyyaml==6.0.3 (from -r /workspace/Aldeci/requirements.txt (line 96))
  Using cached pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.4 kB)
Collecting radon==6.0.1 (from -r /workspace/Aldeci/requirements.txt (line 101))
  Using cached radon-6.0.1-py2.py3-none-any.whl.metadata (8.2 kB)
Collecting referencing==0.36.2 (from -r /workspace/Aldeci/requirements.txt (line 103))
  Using cached referencing-0.36.2-py3-none-any.whl.metadata (2.8 kB)
Collecting requests==2.32.5 (from -r /workspace/Aldeci/requirements.txt (line 107))
  Using cached requests-2.32.5-py3-none-any.whl.metadata (4.9 kB)
Collecting rich==14.2.0 (from -r /workspace/Aldeci/requirements.txt (line 109))
  Using cached rich-14.2.0-py3-none-any.whl.metadata (18 kB)
Collecting rpds-py==0.27.1 (from -r /workspace/Aldeci/requirements.txt (line 113))
  Using cached rpds_py-0.27.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.2 kB)
Collecting semantic-version==2.10.0 (from -r /workspace/Aldeci/requirements.txt (line 117))
  Using cached semantic_version-2.10.0-py2.py3-none-any.whl.metadata (9.7 kB)
Collecting shellingham==1.5.4 (from -r /workspace/Aldeci/requirements.txt (line 119))
  Using cached shellingham-1.5.4-py2.py3-none-any.whl.metadata (3.5 kB)
Collecting six==1.17.0 (from -r /workspace/Aldeci/requirements.txt (line 121))
  Using cached six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting sniffio==1.3.1 (from -r /workspace/Aldeci/requirements.txt (line 123))
  Using cached sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
Collecting starlette==0.48.0 (from -r /workspace/Aldeci/requirements.txt (line 125))
  Using cached starlette-0.48.0-py3-none-any.whl.metadata (6.3 kB)
Collecting structlog==25.4.0 (from -r /workspace/Aldeci/requirements.txt (line 127))
  Using cached structlog-25.4.0-py3-none-any.whl.metadata (7.6 kB)
Collecting typer==0.19.2 (from -r /workspace/Aldeci/requirements.txt (line 129))
  Using cached typer-0.19.2-py3-none-any.whl.metadata (16 kB)
Collecting typing-extensions==4.15.0 (from -r /workspace/Aldeci/requirements.txt (line 131))
  Using cached typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Collecting typing-inspection==0.4.2 (from -r /workspace/Aldeci/requirements.txt (line 141))
  Using cached typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting urllib3==2.5.0 (from -r /workspace/Aldeci/requirements.txt (line 143))
  Using cached urllib3-2.5.0-py3-none-any.whl.metadata (6.5 kB)
Collecting uvicorn==0.37.0 (from uvicorn[standard]==0.37.0->-r /workspace/Aldeci/requirements.txt (line 145))
  Using cached uvicorn-0.37.0-py3-none-any.whl.metadata (6.6 kB)
Collecting uvloop==0.21.0 (from -r /workspace/Aldeci/requirements.txt (line 147))
  Using cached uvloop-0.21.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
Collecting watchfiles==1.1.0 (from -r /workspace/Aldeci/requirements.txt (line 149))
  Using cached watchfiles-1.1.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
Collecting websockets==15.0.1 (from -r /workspace/Aldeci/requirements.txt (line 151))
  Using cached websockets-15.0.1-cp312-cp312-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
Collecting xmlschema==4.1.0 (from -r /workspace/Aldeci/requirements.txt (line 153))
  Using cached xmlschema-4.1.0-py3-none-any.whl.metadata (8.0 kB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached anyio-4.11.0-py3-none-any.whl (109 kB)
Using cached attrs-25.4.0-py3-none-any.whl (67 kB)
Using cached certifi-2025.10.5-py3-none-any.whl (163 kB)
Using cached cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (219 kB)
Using cached charset_normalizer-3.4.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (151 kB)
Using cached click-8.3.0-py3-none-any.whl (107 kB)
Using cached colorama-0.4.6-py2.py3-none-any.whl (25 kB)
Using cached cryptography-46.0.2-cp311-abi3-manylinux_2_34_x86_64.whl (4.5 MB)
Using cached defusedxml-0.7.1-py2.py3-none-any.whl (25 kB)
Using cached elementpath-5.0.4-py3-none-any.whl (245 kB)
Using cached fastapi-0.119.0-py3-none-any.whl (107 kB)
Using cached pydantic-2.12.0-py3-none-any.whl (459 kB)
Using cached starlette-0.48.0-py3-none-any.whl (73 kB)
Using cached fastjsonschema-2.21.2-py3-none-any.whl (24 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (517 kB)
Using cached httpx-0.28.1-py3-none-any.whl (73 kB)
Using cached idna-3.11-py3-none-any.whl (71 kB)
Using cached iniconfig-2.1.0-py3-none-any.whl (6.0 kB)
Using cached jsonschema-4.25.1-py3-none-any.whl (90 kB)
Using cached jsonschema_specifications-2025.9.1-py3-none-any.whl (18 kB)
Using cached lib4sbom-0.8.8-py2.py3-none-any.whl (2.6 MB)
Using cached mando-0.7.1-py2.py3-none-any.whl (28 kB)
Using cached markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Using cached networkx-3.4.2-py3-none-any.whl (1.7 MB)
Using cached numpy-2.2.6-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (16.5 MB)
Using cached packaging-25.0-py3-none-any.whl (66 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached pycparser-2.23-py3-none-any.whl (118 kB)
Using cached pydantic_core-2.41.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.1 MB)
Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
Using cached pytest-8.4.2-py3-none-any.whl (365 kB)
Using cached python_dotenv-1.1.1-py3-none-any.whl (20 kB)
Using cached pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (807 kB)
Using cached radon-6.0.1-py2.py3-none-any.whl (52 kB)
Using cached referencing-0.36.2-py3-none-any.whl (26 kB)
Using cached requests-2.32.5-py3-none-any.whl (64 kB)
Using cached urllib3-2.5.0-py3-none-any.whl (129 kB)
Using cached rich-14.2.0-py3-none-any.whl (243 kB)
Using cached rpds_py-0.27.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (386 kB)
Using cached semantic_version-2.10.0-py2.py3-none-any.whl (15 kB)
Using cached shellingham-1.5.4-py2.py3-none-any.whl (9.8 kB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Using cached sniffio-1.3.1-py3-none-any.whl (10 kB)
Using cached structlog-25.4.0-py3-none-any.whl (68 kB)
Using cached typer-0.19.2-py3-none-any.whl (46 kB)
Using cached typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Using cached typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Using cached uvicorn-0.37.0-py3-none-any.whl (67 kB)
Using cached uvloop-0.21.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (4.7 MB)
Using cached watchfiles-1.1.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (452 kB)
Using cached websockets-15.0.1-cp312-cp312-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (182 kB)
Using cached xmlschema-4.1.0-py3-none-any.whl (458 kB)
Saved ./wheels/annotated_types-0.7.0-py3-none-any.whl
Saved ./wheels/anyio-4.11.0-py3-none-any.whl
Saved ./wheels/attrs-25.4.0-py3-none-any.whl
Saved ./wheels/certifi-2025.10.5-py3-none-any.whl
Saved ./wheels/cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
Saved ./wheels/charset_normalizer-3.4.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
Saved ./wheels/click-8.3.0-py3-none-any.whl
Saved ./wheels/colorama-0.4.6-py2.py3-none-any.whl
Saved ./wheels/cryptography-46.0.2-cp311-abi3-manylinux_2_34_x86_64.whl
Saved ./wheels/defusedxml-0.7.1-py2.py3-none-any.whl
Saved ./wheels/elementpath-5.0.4-py3-none-any.whl
Saved ./wheels/fastapi-0.119.0-py3-none-any.whl
Saved ./wheels/pydantic-2.12.0-py3-none-any.whl
Saved ./wheels/starlette-0.48.0-py3-none-any.whl
Saved ./wheels/fastjsonschema-2.21.2-py3-none-any.whl
Saved ./wheels/h11-0.16.0-py3-none-any.whl
Saved ./wheels/httpcore-1.0.9-py3-none-any.whl
Saved ./wheels/httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl
Saved ./wheels/httpx-0.28.1-py3-none-any.whl
Saved ./wheels/idna-3.11-py3-none-any.whl
Saved ./wheels/iniconfig-2.1.0-py3-none-any.whl
Saved ./wheels/jsonschema-4.25.1-py3-none-any.whl
Saved ./wheels/jsonschema_specifications-2025.9.1-py3-none-any.whl
Saved ./wheels/lib4sbom-0.8.8-py2.py3-none-any.whl
Saved ./wheels/mando-0.7.1-py2.py3-none-any.whl
Saved ./wheels/markdown_it_py-4.0.0-py3-none-any.whl
Saved ./wheels/mdurl-0.1.2-py3-none-any.whl
Saved ./wheels/networkx-3.4.2-py3-none-any.whl
Saved ./wheels/numpy-2.2.6-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
Saved ./wheels/packaging-25.0-py3-none-any.whl
Saved ./wheels/pluggy-1.6.0-py3-none-any.whl
Saved ./wheels/pycparser-2.23-py3-none-any.whl
Saved ./wheels/pydantic_core-2.41.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
Saved ./wheels/pygments-2.19.2-py3-none-any.whl
Saved ./wheels/pytest-8.4.2-py3-none-any.whl
Saved ./wheels/python_dotenv-1.1.1-py3-none-any.whl
Saved ./wheels/pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
Saved ./wheels/radon-6.0.1-py2.py3-none-any.whl
Saved ./wheels/referencing-0.36.2-py3-none-any.whl
Saved ./wheels/requests-2.32.5-py3-none-any.whl
Saved ./wheels/urllib3-2.5.0-py3-none-any.whl
Saved ./wheels/rich-14.2.0-py3-none-any.whl
Saved ./wheels/rpds_py-0.27.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
Saved ./wheels/semantic_version-2.10.0-py2.py3-none-any.whl
Saved ./wheels/shellingham-1.5.4-py2.py3-none-any.whl
Saved ./wheels/six-1.17.0-py2.py3-none-any.whl
Saved ./wheels/sniffio-1.3.1-py3-none-any.whl
Saved ./wheels/structlog-25.4.0-py3-none-any.whl
Saved ./wheels/typer-0.19.2-py3-none-any.whl
Saved ./wheels/typing_extensions-4.15.0-py3-none-any.whl
Saved ./wheels/typing_inspection-0.4.2-py3-none-any.whl
Saved ./wheels/uvicorn-0.37.0-py3-none-any.whl
Saved ./wheels/uvloop-0.21.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
Saved ./wheels/watchfiles-1.1.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
Saved ./wheels/websockets-15.0.1-cp312-cp312-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl
Saved ./wheels/xmlschema-4.1.0-py3-none-any.whl
```

## Install Test

```text
Looking in links: /workspace/Aldeci/wheels
Processing ./wheels/annotated_types-0.7.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 7))
Processing ./wheels/anyio-4.11.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 9))
Processing ./wheels/attrs-25.4.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 14))
Processing ./wheels/certifi-2025.10.5-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 18))
Processing ./wheels/cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 23))
Processing ./wheels/charset_normalizer-3.4.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 25))
Processing ./wheels/click-8.3.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 27))
Processing ./wheels/colorama-0.4.6-py2.py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 31))
Processing ./wheels/cryptography-46.0.2-cp311-abi3-manylinux_2_34_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 33))
Processing ./wheels/defusedxml-0.7.1-py2.py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 35))
Processing ./wheels/elementpath-5.0.4-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 37))
Processing ./wheels/fastapi-0.119.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 39))
Processing ./wheels/fastjsonschema-2.21.2-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 41))
Processing ./wheels/h11-0.16.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 43))
Processing ./wheels/httpcore-1.0.9-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 47))
Processing ./wheels/httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 49))
Processing ./wheels/httpx-0.28.1-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 51))
Processing ./wheels/idna-3.11-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 53))
Processing ./wheels/iniconfig-2.1.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 58))
Processing ./wheels/jsonschema-4.25.1-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 60))
Processing ./wheels/jsonschema_specifications-2025.9.1-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 62))
Processing ./wheels/lib4sbom-0.8.8-py2.py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 64))
Processing ./wheels/mando-0.7.1-py2.py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 66))
Processing ./wheels/markdown_it_py-4.0.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 68))
Processing ./wheels/mdurl-0.1.2-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 70))
Processing ./wheels/networkx-3.4.2-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 72))
Processing ./wheels/numpy-2.2.6-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 74))
Processing ./wheels/packaging-25.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 76))
Processing ./wheels/pluggy-1.6.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 78))
Processing ./wheels/pycparser-2.23-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 80))
Processing ./wheels/pydantic-2.12.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 82))
Processing ./wheels/pydantic_core-2.41.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 86))
Processing ./wheels/pygments-2.19.2-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 88))
Processing ./wheels/pytest-8.4.2-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 92))
Processing ./wheels/python_dotenv-1.1.1-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 94))
Processing ./wheels/pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 96))
Processing ./wheels/radon-6.0.1-py2.py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 101))
Processing ./wheels/referencing-0.36.2-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 103))
Processing ./wheels/requests-2.32.5-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 107))
Processing ./wheels/rich-14.2.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 109))
Processing ./wheels/rpds_py-0.27.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 113))
Processing ./wheels/semantic_version-2.10.0-py2.py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 117))
Processing ./wheels/shellingham-1.5.4-py2.py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 119))
Processing ./wheels/six-1.17.0-py2.py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 121))
Processing ./wheels/sniffio-1.3.1-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 123))
Processing ./wheels/starlette-0.48.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 125))
Processing ./wheels/structlog-25.4.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 127))
Processing ./wheels/typer-0.19.2-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 129))
Processing ./wheels/typing_extensions-4.15.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 131))
Processing ./wheels/typing_inspection-0.4.2-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 141))
Processing ./wheels/urllib3-2.5.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 143))
Processing ./wheels/uvicorn-0.37.0-py3-none-any.whl (from uvicorn[standard]==0.37.0->-r /workspace/Aldeci/requirements.txt (line 145))
Processing ./wheels/uvloop-0.21.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 147))
Processing ./wheels/watchfiles-1.1.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 149))
Processing ./wheels/websockets-15.0.1-cp312-cp312-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (from -r /workspace/Aldeci/requirements.txt (line 151))
Processing ./wheels/xmlschema-4.1.0-py3-none-any.whl (from -r /workspace/Aldeci/requirements.txt (line 153))
Installing collected packages: fastjsonschema, websockets, uvloop, urllib3, typing-extensions, structlog, sniffio, six, shellingham, semantic-version, rpds-py, pyyaml, python-dotenv, pygments, pycparser, pluggy, packaging, numpy, networkx, mdurl, iniconfig, idna, httptools, h11, elementpath, defusedxml, colorama, click, charset-normalizer, certifi, attrs, annotated-types, xmlschema, uvicorn, typing-inspection, requests, referencing, pytest, pydantic-core, markdown-it-py, mando, httpcore, cffi, anyio, watchfiles, starlette, rich, radon, pydantic, jsonschema-specifications, httpx, cryptography, typer, jsonschema, fastapi, lib4sbom
Successfully installed annotated-types-0.7.0 anyio-4.11.0 attrs-25.4.0 certifi-2025.10.5 cffi-2.0.0 charset-normalizer-3.4.3 click-8.3.0 colorama-0.4.6 cryptography-46.0.2 defusedxml-0.7.1 elementpath-5.0.4 fastapi-0.119.0 fastjsonschema-2.21.2 h11-0.16.0 httpcore-1.0.9 httptools-0.7.1 httpx-0.28.1 idna-3.11 iniconfig-2.1.0 jsonschema-4.25.1 jsonschema-specifications-2025.9.1 lib4sbom-0.8.8 mando-0.7.1 markdown-it-py-4.0.0 mdurl-0.1.2 networkx-3.4.2 numpy-2.2.6 packaging-25.0 pluggy-1.6.0 pycparser-2.23 pydantic-2.12.0 pydantic-core-2.41.1 pygments-2.19.2 pytest-8.4.2 python-dotenv-1.1.1 pyyaml-6.0.3 radon-6.0.1 referencing-0.36.2 requests-2.32.5 rich-14.2.0 rpds-py-0.27.1 semantic-version-2.10.0 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 starlette-0.48.0 structlog-25.4.0 typer-0.19.2 typing-extensions-4.15.0 typing-inspection-0.4.2 urllib3-2.5.0 uvicorn-0.37.0 uvloop-0.21.0 watchfiles-1.1.0 websockets-15.0.1 xmlschema-4.1.0
```
