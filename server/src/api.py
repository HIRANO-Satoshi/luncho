'''
  Luncho API

  @author HIRANO Satoshi
  @date  2021/05/13
'''

import json
import copy
import datetime
import logging
import pdb
from typing import List, Dict, Tuple, Union, Any, Type, Generator, Optional, ClassVar, cast

from fastapi import Header, APIRouter
from fastapi.openapi.utils import get_openapi
from fastapi_utils.openapi import simplify_operation_ids

from conf import SDR_Per_Luncho
from src import exchange_rate
from src.utils import error
from src.ppp_data import Countries, CountryCode_Names
from src.types import Currency, CurrencyCode, C1000, CountryCode, LunchoData, Country

api_router = APIRouter()

@api_router.get("/luncho-data", response_model=LunchoData, tags=['Luncho'])
async def lunchoData(
        country_code: CountryCode, # client provided country code in ISO-3166-1-2 formant like 'JP'
) -> LunchoData:
    '''
      Returns LunchoData that is needed to convert between Luncho and local currency of the countryCode.
      Data size is about 400 bytes.
    '''
    country: Optional[Country] = Countries.get(country_code, None)
    if not country:
        error(country_code, 'Invalid country code')
        # never come here

    return country


@api_router.get("/countries", response_model=Dict[CountryCode, str], tags=['Luncho'])
async def countries() -> Dict[CountryCode, str]:
    '''
      Returns a dict of supported country codes and names so that you can show
    a dropdown list of countries. Data size is about 3.5KB.
       E.g. {'JP': 'Japan', 'US': 'United States'...}.
    '''
    return CountryCode_Names


@api_router.get("/luncho-datas", response_model=Dict[CountryCode, LunchoData], tags=['Luncho'])
async def lunchoDatas() -> Dict[CountryCode, LunchoData]:
    '''
      Returns A list of LunchoDatas for all supported countries. Data size is about 40KB.
    '''

    return Countries



# use method names in OpenAPI operationIds to generate methods with the method names
simplify_operation_ids(api_router)
