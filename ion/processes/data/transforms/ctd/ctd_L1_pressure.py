'''
@author MManning
@file ion/processes/data/transforms/ctd/ctd_L1_pressure.py
@description Transforms CTD parsed data into L1 product for pressure
'''

from pyon.ion.transform import TransformFunction, TransformDataProcess
from pyon.service.service import BaseService
from pyon.core.exception import BadRequest
from pyon.public import IonObject, RT, log
import numpy as np

from prototype.sci_data.stream_defs import L1_pressure_stream_definition, L0_pressure_stream_definition

from prototype.sci_data.stream_parser import PointSupplementStreamParser
from prototype.sci_data.constructor_apis import PointSupplementConstructor

### For new granule and stream interface
from ion.services.dm.utility.granule.record_dictionary import RecordDictionaryTool
from ion.services.dm.utility.granule.granule import build_granule
from pyon.util.containers import get_safe
from coverage_model.parameter import ParameterDictionary, ParameterContext
from coverage_model.parameter_types import QuantityType
from coverage_model.basic_types import AxisTypeEnum
from ion.services.dm.utility.granule_utils import CoverageCraft

craft = CoverageCraft
sdom, tdom = craft.create_domains()
sdom = sdom.dump()
tdom = tdom.dump()
parameter_dictionary = craft.create_parameters()

class CTDL1PressureTransform(TransformFunction):
    ''' A basic transform that receives input through a subscription,
    parses the input from a CTD, extracts the pressure vaule and scales it accroding to
    the defined algorithm. If the transform
    has an output_stream it will publish the output on the output stream.

    '''

    # Make the stream definitions of the transform class attributes... best available option I can think of?
    incoming_stream_def = L0_pressure_stream_definition()
    outgoing_stream_def = L1_pressure_stream_definition()

    def __init__(self):
        super(CTDL1PressureTransform, self).__init__()


    def execute(self, granule):
        """Processes incoming data!!!!
        """

        rdt = RecordDictionaryTool.load_from_granule(granule)
        #todo: use only flat dicts for now, may change later...
#        rdt0 = rdt['coordinates']
#        rdt1 = rdt['data']

        pressure = get_safe(rdt, 'pressure') #psd.get_values('conductivity')

        longitude = get_safe(rdt, 'lon') # psd.get_values('longitude')
        latitude = get_safe(rdt, 'lat')  #psd.get_values('latitude')
        time = get_safe(rdt, 'time') # psd.get_values('time')
        depth = get_safe(rdt, 'depth') # psd.get_values('time')

        log.warn('Got pressure: %s' % str(pressure))


        # L1
        # 1) The algorithm input is the L0 pressure data product (p_hex) and, in the case of the SBE 37IM, the pressure range (P_rng) from metadata.
        # 2) Convert the hexadecimal string to a decimal string
        # 3) For the SBE 37IM only, convert the pressure range (P_rng) from psia to dbar SBE 37IM
        #    Convert P_rng (input from metadata) from psia to dbar
        # 4) Perform scaling operation
        #    SBE 37IM
        #    L1 pressure data product (in dbar):


        # Use the constructor to put data into a granule
        psc = PointSupplementConstructor(point_definition=self.outgoing_stream_def, stream_id=self.streams['output'])
        ### Assumes the config argument for output streams is known and there is only one 'output'.
        ### the stream id is part of the metadata which much go in each stream granule - this is awkward to do at the
        ### application level like this!

        scaled_pressure = pressure

        for i in xrange(len(pressure)):
            #todo: get pressure range from metadata (if present) and include in calc
            scaled_pressure[i] = ( pressure[i])

        root_rdt = RecordDictionaryTool(param_dictionary=parameter_dictionary)

        root_rdt['pressure'] = scaled_pressure
        root_rdt['time'] = time
        root_rdt['lat'] = latitude
        root_rdt['lon'] = longitude
        root_rdt['depth'] = depth

#        root_rdt['coordinates'] = coord_rdt
#        root_rdt['data'] = data_rdt

        return build_granule(data_producer_id='ctd_L1_pressure', param_dictionary=parameter_dictionary, record_dictionary=root_rdt)

        return psc.close_stream_granule()

  