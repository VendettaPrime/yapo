import unittest
import yapo
import numpy as np


class PortfolioAssetStatisticsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.asset_name = 'nlu/922'
        cls.asset = yapo.portfolio_asset(name=cls.asset_name,
                                         start_period='2011-1', end_period='2017-2', currency='USD')
        cls.places = 4

    def test__accumulated_rate_of_return(self):
        arors = self.asset.rate_of_return(kind='accumulated').values
        self.assertAlmostEqual(arors.max(), .0924, places=self.places)
        self.assertAlmostEqual(arors.min(), -.5464, places=self.places)

        arors_real = self.asset.rate_of_return(kind='accumulated', real=True).values
        self.assertAlmostEqual(arors_real.max(), .0765, places=self.places)
        self.assertAlmostEqual(arors_real.min(), -.5725, places=self.places)

    def test__handle_related_inflation(self):
        self.assertRaises(Exception, self.asset.inflation, kind='abracadabra')

        self.assertAlmostEqual(self.asset.inflation(kind='accumulated').value, .1062, places=self.places)
        self.assertAlmostEqual(self.asset.inflation(kind='a_mean').value, 0.0014, places=self.places)
        self.assertAlmostEqual(self.asset.inflation(kind='g_mean').value, 0.0167, places=self.places)

        self.assertEqual(self.asset.inflation(kind='values').size,
                         self.asset.rate_of_return().size)

    def test__compound_annual_growth_rate(self):
        cagr_default = self.asset.compound_annual_growth_rate()
        self.assertAlmostEqual(cagr_default.value, -.0562, places=self.places)

        cagr_long_time = self.asset.compound_annual_growth_rate(years_ago=20)
        self.assertAlmostEqual(cagr_long_time.value, cagr_default.value, places=self.places)

        cagr_one_year = self.asset.compound_annual_growth_rate(years_ago=1)
        self.assertAlmostEqual(cagr_one_year.value, .4738, places=self.places)

        cagr_default1, cagr_long_time1, cagr_one_year1 = \
            self.asset.compound_annual_growth_rate(years_ago=[None, 20, 1])
        self.assertAlmostEqual(cagr_default1.value, cagr_default.value, places=self.places)
        self.assertAlmostEqual(cagr_long_time1.value, cagr_long_time.value, places=self.places)
        self.assertAlmostEqual(cagr_one_year1.value, cagr_one_year.value, places=self.places)

    def test__compound_annual_growth_rate_real(self):
        cagr_default = self.asset.compound_annual_growth_rate(real=True)
        self.assertAlmostEqual(cagr_default.value, -.0717, places=self.places)

        cagr_long_time = self.asset.compound_annual_growth_rate(years_ago=20, real=True)
        self.assertAlmostEqual(cagr_default.value, cagr_long_time.value, places=self.places)

        cagr_one_year = self.asset.compound_annual_growth_rate(years_ago=1, real=True)
        self.assertAlmostEqual(cagr_one_year.value, .4345, places=self.places)

        cagr_default1, cagr_long_time1, cagr_one_year1 = \
            self.asset.compound_annual_growth_rate(years_ago=[None, 20, 1], real=True)
        self.assertAlmostEqual(cagr_default1.value, cagr_default.value, places=self.places)
        self.assertAlmostEqual(cagr_long_time1.value, cagr_long_time.value, places=self.places)
        self.assertAlmostEqual(cagr_one_year1.value, cagr_one_year.value, places=self.places)

    def test__risk(self):
        short_asset = yapo.portfolio_asset(name=self.asset_name,
                                           start_period='2016-8', end_period='2016-12', currency='USD')

        self.assertRaises(Exception, short_asset.risk, period='year')
        self.assertAlmostEqual(self.asset.risk().value, .2950, places=self.places)
        self.assertAlmostEqual(self.asset.risk(period='year').value, .2950, places=self.places)
        self.assertAlmostEqual(self.asset.risk(period='month').value, .0846, places=self.places)

    def test__inflation(self):
        self.assertRaises(Exception, self.asset.inflation, kind='abracadabra')

        self.assertAlmostEqual(self.asset.inflation(kind='accumulated').value, .1062, places=self.places)
        self.assertAlmostEqual(self.asset.inflation(kind='a_mean').value, .0014, places=self.places)
        self.assertAlmostEqual(self.asset.inflation(kind='g_mean').value, .0167, places=self.places)

        self.assertEqual(self.asset.inflation(kind='values').size,
                         self.asset.rate_of_return().size)
