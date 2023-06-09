import warnings
import json
import os
import pytz
from sqlalchemy import create_engine
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
import InstrumentComLib as icl

def locdb_engine():
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, '.env'))
    daqdbuser = os.environ.get('systemTag')
    daqdbpassword = os.environ.get('daqdbPassword')
    daqdbhost = os.environ.get('daqdbHost')
    daqdbport = os.environ.get('daqdbPort')
    engine = create_engine(f'postgresql://{daqdbuser}:{daqdbpassword}@{daqdbhost}:{daqdbport}/daqdb')
    return engine

def tsdb_engine():
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, '.env'))
    tsdbuser = os.environ.get('systemTag')
    tsdbpassword = os.environ.get('tsdbPassword')
    tsdbhost = os.environ.get('tsdbHost')
    tsdbport = os.environ.get('tsdbPort')
    engine = create_engine(f'postgresql://{tsdbuser}:{tsdbpassword}@{tsdbhost}:{tsdbport}/daqdb')
    return engine

class System:
    def __init__(self, write_frequency=None):
        BASEDIR = os.path.abspath(os.path.dirname(__file__))
        load_dotenv(os.path.join(BASEDIR, '.env'))
        self._tag = os.environ.get('systemTag')
        self._name = os.environ.get('systemName')
        self._timezone = os.environ.get('systemTZ')
        self._devices = []
        self._writers = []
        self._data = None
        self._write_frequency = write_frequency
        self._last_write_time = None
        self.getconfig()
    
    @property
    def tag(self):
        return self._tag
    
    @property
    def name(self):
        return self._name
    
    @property
    def devices(self):
        return self._devices

    @property
    def instruments(self):
        instruments = []
        for device in self.devices:
            instruments = instruments + device.instruments
        return instruments

    @property
    def timezone(self):
        return self._timezone

    @property
    def data(self):
        return self._data

    @property
    def write_frequency(self):
        return self._write_frequency

    @property
    def last_write_time(self):
        return self._last_write_time

    @property
    def ready_to_write(self):
        if self.last_write_time == None:
            return True
        elif self.write_frequency == None:
            return False
        else:
            tdelta = (datetime.now(pytz.timezone(self.timezone)) - self.last_write_time).seconds
            ready_to_write = tdelta >= self.write_frequency
            return ready_to_write

    def set_write_frequency(self, write_frequency: int):
        self._write_frequency = write_frequency

    @property
    def writers(self):
        return self._writers

    def add_writer(self, writer):
        assert isinstance(writer, Writer), f"Writer to add to system must be {type(Writer)} Object"
        if writer not in self._writers:
            self._writers.append(writer)

    def write_to_db(self):
        if self.ready_to_write:
            # convert most recent row in self.data to long format then pass to writers
            tags = self.data.columns
            values = self.data.iloc[-1].values
            t_stamp = self.data.index[-1]
            long_df = pd.DataFrame(data={'t_stamp':t_stamp, 'tag':tags, 'value':values})
            for writer in self.writers:
                writer.write(long_df)
                if writer.status == 1:
                    self._last_write_time = t_stamp.to_pydatetime()
        else: pass

    def getconfig(self):
        with open('systemconfig.json') as f:
            config = json.loads(f.read())
        instruments = config['instruments']
        devices = config['devices']
        for dev in devices:
            device = Device(**dev)
            for inst in instruments:
                instrument = Instrument(**inst)
                if instrument.device == device.name:
                    device._instruments = device.instruments + [instrument]
            self._devices.append(device)

    def writeconfig(self):
        pass

    def initialize(self):
        # Connect to all devices
        for device in self.devices:
            device.connect()
        # Create local writer
        local_writer = Writer(name='Local DB Write', engine=locdb_engine())
        self.add_writer(local_writer)
        network_writer = Writer(name="Network DB Write", engine = tsdb_engine())
        self.add_writer(network_writer)

    def read_all(self):
        #maximum time to keep in system dataframe memory
        max_df_length = timedelta(seconds=3600)
        for device in self.devices:
            device_data = device.read()
            # set raw values for instruments on device
            for instrument in device.instruments:
                instrument._raw = device_data[instrument.tag][0]
        # append row to system.data dataframe
        self.update_ts_data()

    def update_ts_data(self):
        # maximum time to keep in system dataframe memory
        max_df_length = timedelta(seconds=3600)
        time = datetime.now(pytz.timezone(self.timezone))
        newdata = pd.DataFrame({inst.tag_label:[inst.pv] for inst in self.instruments}, index=[time])
        if self._data is None:
            # first read, self.data does not exist
            self._data = pd.DataFrame({inst.tag_label:[] for inst in self.instruments})
            self._data = pd.concat([self._data, newdata])
        else:
            #dataframe already exists, append read data
            self._data = pd.concat([self._data, newdata])
            # Drop rows older than max_df_length
            self._data = self.data.drop(index=filter(lambda x: x < time - max_df_length, self.data.index))

    # def read_all(self):
    #     data = pd.DataFrame(index = [0])
    #     #maximum time to keep in system dataframe memory
    #     max_df_length = timedelta(seconds=3600)
    #     for device in self.devices:
    #         device_data = device.read()
    #         #scale data before joining
    #         scaled_data = device_data
    #         for col in scaled_data.columns:
    #             scale_factor = .1
    #             scaled_data[col] = scaled_data[col] * scale_factor
    #         data = data.join(scaled_data)
    #         # set raw values for instruments on device
    #         for instrument in device.instruments:
    #             instrument._raw = data[instrument.tag][0]
    #     # append row to system.data dataframe
    #     time = datetime.now(pytz.timezone(self.timezone))
    #     data.index = [time]
    #     if self._data is None:
    #         #dataframe does not exist before first read
    #         self._data = data
    #     else:
    #         #dataframe already exists, append read data
    #         self._data = pd.concat([self._data, data])
    #         self._data = self.data.drop(index=filter(lambda x: x < time - max_df_length, self.data.index))
    #     return data
class Device:
    def __init__(self, type=None, name=None, connection_params={}, connection=None, instruments=[], **kwargs):
        self._type = type
        self._name = name
        self._connection_params = connection_params
        self._connection = connection
        self._instruments = instruments

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def connection_params(self):
        return self._connection_params

    @property
    def connection(self):
        return self._connection

    @property
    def instruments(self):
        return self._instruments

    def connect(self):
        self._connection = icl.connect(self)

    def read(self):
        return icl.read(self)


class Instrument:
    def __init__(self, device=None, channel=None, tag=None, tag_label=None, measure=None, unit=None, raw=None,
                 slave=None, raw_high=None, raw_low=None, eng_high=None, eng_low=None, **kwargs):
        self._device = device
        self._channel = channel
        self._slave = slave
        self._tag = tag
        self._tag_label = tag_label
        self._measure = measure
        self._unit = unit
        self._raw_high = raw_high
        self._raw_low = raw_low
        self._eng_high = eng_high
        self._eng_low = eng_low
        self._raw = raw

    @property
    def device(self):
        return self._device

    @property
    def channel(self):
        return self._channel

    @property
    def slave(self):
        return self._slave

    @property
    def tag(self):
        return self._tag

    @property
    def tag_label(self):
        return self._tag_label

    @property
    def measure(self):
        return self._measure

    @property
    def unit(self):
        return self._unit

    @property
    def raw(self):
        return self._raw

    @property
    def eng_high(self):
        return self._eng_high

    @property
    def eng_low(self):
        return self._eng_low

    @property
    def raw_high(self):
        return self._raw_high

    @property
    def raw_low(self):
        return self._raw_low
    @property
    def pv(self):
        # process value
        return self.raw * (self.eng_high - self.eng_low)/(self.raw_high - self.raw_low)


class Writer:
    def __init__(self, name: str, type='database', engine=None, filename=None, frequency=30):
        self._type = type
        self._engine = engine
        self._frequency = frequency
        self._last_write_time = pd.NaT
        self._status = -1
        self._name = name
        if self.type == 'database':
            assert self._engine is not None, "Must provide database engine for database writer"
        elif self.type == 'csv':
            assert self._filename is not None, "Must provide filename for csv writer"
        else:
            raise Exception("Writer type must be 'database' or 'csv'")

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def engine(self):
        return self._engine

    @property
    def status(self):
        # -1 not connected
        # 0 last write failed
        # 1 last write success
        return self._status

    @property
    def last_write_time(self):
        return self._last_write_time

    def write(self, df: pd.DataFrame):
        if self.type == 'database':
            try:
                df.to_sql('timeseriesdata', self.engine, if_exists='append', index=False)
                # write succeeded, set last_write_time and set status to 1
                self._last_write_time = df['t_stamp'].loc[0]
                self._status = 1
            except:
                # write failed, set status to 0
                self._status = 0
        elif self.type == 'csv':
            pass

    
