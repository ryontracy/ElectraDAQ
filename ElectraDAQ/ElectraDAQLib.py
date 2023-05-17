import warnings
import json
import os
import re
import pandas as pd
import numpy as np
import scipy.integrate as integrate
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pytz import timezone

def locdb_engine():
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, '.env'))
    tsdbuser = os.environ.get('daqdbUser')
    tsdbpassword = os.environ.get('daqdbPassword')
    tsdbhost = os.environ.get('daqdbHost')
    tsdbport = os.environ.get('daqdbPort')
    engine = create_engine(f'postgresql://{tsdbuser}:{tsdbpassword}@{tsdbhost}:{tsdbport}/daqdb')
    return engine
