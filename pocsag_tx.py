#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: POCSAG TX
# Author: VHMG
# GNU Radio version: 3.10.11.0

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import iio
from gnuradio.filter import pfb
import numpy as np
import pocsag_tx_pocsag_numeric as pocsag_numeric  # embedded python block
import threading




class pocsag_tx(gr.top_block):

    def __init__(self, ric=548579):
        gr.top_block.__init__(self, "POCSAG TX", catch_exceptions=True)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################
        self.ric = ric

        ##################################################
        # Variables
        ##################################################
        self.tx_gain = tx_gain = 0
        self.symrate = symrate = 38400
        self.samp_rate = samp_rate = 2_000_000
        self.pocsagbitrate = pocsagbitrate = 1200
        self.pagerfreq = pagerfreq = 161_125_000
        self.max_deviation = max_deviation = 4500.0
        self.af_gain = af_gain = 190

        ##################################################
        # Blocks
        ##################################################

        self.pocsag_numeric = pocsag_numeric.pocsagsender(number=ric, text="02-{246}-4070U")
        self.pfb_arb_resampler_xxx_0 = pfb.arb_resampler_ccf(
            (float(samp_rate)/float(symrate)),
            taps=None,
            flt_size=16,
            atten=100)
        self.pfb_arb_resampler_xxx_0.declare_sample_delay(0)
        self.iio_pluto_sink_0 = iio.fmcomms2_sink_fc32('ip:192.168.10.1' if 'ip:192.168.10.1' else iio.get_pluto_uri(), [True, True], 32768, False)
        self.iio_pluto_sink_0.set_len_tag_key('')
        self.iio_pluto_sink_0.set_bandwidth(2_000_000)
        self.iio_pluto_sink_0.set_frequency(int(pagerfreq))
        self.iio_pluto_sink_0.set_samplerate(samp_rate)
        self.iio_pluto_sink_0.set_attenuation(0, 20)
        self.iio_pluto_sink_0.set_filter_params('Auto', '', 5e3, 6e3)
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_char*1, (int(symrate/pocsagbitrate)))
        self.blocks_char_to_float_0 = blocks.char_to_float(1, (af_gain*0.7/1000))
        self.analog_frequency_modulator_fc_0 = analog.frequency_modulator_fc((2.0 * np.pi * max_deviation / float(symrate)))


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_frequency_modulator_fc_0, 0), (self.pfb_arb_resampler_xxx_0, 0))
        self.connect((self.blocks_char_to_float_0, 0), (self.analog_frequency_modulator_fc_0, 0))
        self.connect((self.blocks_repeat_0, 0), (self.blocks_char_to_float_0, 0))
        self.connect((self.pfb_arb_resampler_xxx_0, 0), (self.iio_pluto_sink_0, 0))
        self.connect((self.pocsag_numeric, 0), (self.blocks_repeat_0, 0))


    def get_ric(self):
        return self.ric

    def set_ric(self, ric):
        self.ric = ric
        self.pocsag_numeric.number = self.ric

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain

    def get_symrate(self):
        return self.symrate

    def set_symrate(self, symrate):
        self.symrate = symrate
        self.analog_frequency_modulator_fc_0.set_sensitivity((2.0 * np.pi * self.max_deviation / float(self.symrate)))
        self.blocks_repeat_0.set_interpolation((int(self.symrate/self.pocsagbitrate)))
        self.pfb_arb_resampler_xxx_0.set_rate((float(self.samp_rate)/float(self.symrate)))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.iio_pluto_sink_0.set_samplerate(self.samp_rate)
        self.pfb_arb_resampler_xxx_0.set_rate((float(self.samp_rate)/float(self.symrate)))

    def get_pocsagbitrate(self):
        return self.pocsagbitrate

    def set_pocsagbitrate(self, pocsagbitrate):
        self.pocsagbitrate = pocsagbitrate
        self.blocks_repeat_0.set_interpolation((int(self.symrate/self.pocsagbitrate)))

    def get_pagerfreq(self):
        return self.pagerfreq

    def set_pagerfreq(self, pagerfreq):
        self.pagerfreq = pagerfreq
        self.iio_pluto_sink_0.set_frequency(int(self.pagerfreq))

    def get_max_deviation(self):
        return self.max_deviation

    def set_max_deviation(self, max_deviation):
        self.max_deviation = max_deviation
        self.analog_frequency_modulator_fc_0.set_sensitivity((2.0 * np.pi * self.max_deviation / float(self.symrate)))

    def get_af_gain(self):
        return self.af_gain

    def set_af_gain(self, af_gain):
        self.af_gain = af_gain
        self.blocks_char_to_float_0.set_scale((self.af_gain*0.7/1000))



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-R", "--ric", dest="ric", type=intx, default=548579,
        help="Set RIC [default=%(default)r]")
    return parser


def main(top_block_cls=pocsag_tx, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(ric=options.ric)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    tb.flowgraph_started.set()

    tb.wait()


if __name__ == '__main__':
    main()
