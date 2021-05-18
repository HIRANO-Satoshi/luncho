#!/usr/local/bin/pypy3
'''
  Luncho server

  @author HIRANO Satoshi
  @date  2020/02/28
'''

#import pdb
#import logging
import os
import sys
import json
import logging
from typing import List, Dict, Optional

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

#pylint: disable=wrong-import-position
import conf
from src import api, ppp_data, exchange_rate

root = logging.getLogger()
root.setLevel(logging.INFO)
#root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler2 = logging.StreamHandler(sys.stderr)
handler2.setLevel(logging.ERROR)
root.addHandler(handler)
root.addHandler(handler2) # error logs

app = FastAPI(
    title="Luncho server converts between local currency and Universal Luncho index for the economic inequality problem",
    description="With 100 Luncho, you can have simple lunch in every country.",
    version="0.0.1",
    openapi_tags=[
        {
            "name": "Luncho",
            "description": "Luncho calculation APIs.",
        },
        # admin API
    ]
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*", # "http://localhost:8082",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# static files in static dir
#app.mount("/static", StaticFiles(directory="static"), name="static")

def gen_openapi_schema() -> Dict:
    ''' Callback for generating OpenAPI schema. '''

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Client library for Luncho API. ",
        version="0.0.1",
        description="Use luncho.ts and luncho.py rather than LunchoAPI.ts and others.",
        routes=app.routes,
    )
    # openapi_schema["info"]["x-logo"] = {
    #     "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    # }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

if __name__ == "__main__":
    # command line
    if len(sys.argv) == 2 and sys.argv[1] == 'gen':
        # gen client library using openAPI generator if schema file is old.

        app.include_router(api.api_router, prefix=conf.API_V1_STR)
        schema: str = json.dumps(gen_openapi_schema())
        old_schema: str = ''
        try:
            with open(conf.Openapi_Schema_File, 'r') as infile:
                old_schema = infile.read()
        except:
            pass

        lib_paths: List[str] = [typ + '-api' for typ, opt in conf.Gen_Openapi.items()]
        if schema != old_schema or not all([os.path.exists(path) for path in lib_paths]): #XXX always true?
            # generate schema file
            with open(conf.Openapi_Schema_File, 'w') as outfile:
                outfile.write(schema)
            print(conf.Openapi_Schema_File + ' was generated.', file=sys.stderr)

            # #  'typescript-aurelia' is always generated for the Aurelia app
            # os.system('npx @openapitools/openapi-generator-cli generate -i ' + conf.Openapi_Schema_File + ' -g typescript-aurelia -o ../app/src/gen-openapi --additional-properties=supportsES6=true,modelPropertyNaming=original')

            # gen client libraries using openAPI generator
            for typ, opt in conf.Gen_Openapi.items():  #type: str, Optional[str]
                cmd = 'npx @openapitools/openapi-generator-cli generate -i ' + conf.Openapi_Schema_File + ' -g ' + typ + ' -o ../client-libs/luncho_' + typ + ' --package-name luncho_' + typ + ' "--additional-properties=modelPropertyNaming=original,' + (opt if opt else '') + '"'
                print(cmd, file=sys.stderr, flush=True)
                os.system(cmd)
    else:
        print('To start Luncho server, just run start-gunicorn.py ', file=sys.stderr)
        print('pypy3 main.py gen    generate client library using openAPI generator', file=sys.stderr)

def init(use_dummy_data=False):
    ''' Called from gunicorn_config.py '''

    # initialize routes
    app.include_router(api.api_router, prefix=conf.API_V1_STR)

    # load exchange rates at startup and every one hour
    logging.info('main.init()')
    ppp_data.init(use_dummy_data=use_dummy_data)
    exchange_rate.init(use_dummy_data)
