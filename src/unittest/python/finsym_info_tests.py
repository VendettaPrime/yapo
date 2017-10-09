import unittest

import yapo
from model.Enums import Currency, SecurityType, Period


class AssetsTest(unittest.TestCase):

    def test_micex_stocks_should_have_correct_fields(self):
        info = yapo.information('micex/SBER')
        self.assertEqual(info.namespace, 'micex')
        self.assertEqual(info.ticker, 'SBER')
        self.assertEqual(info.isin, 'RU0009029540')
        self.assertEqual(info.short_name, 'Сбербанк')
        self.assertEqual(info.long_name, 'Сбербанк России ПАО ао')
        self.assertEqual(info.exchange, 'MICEX')
        self.assertEqual(info.currency, Currency.RUB)
        self.assertEqual(info.security_type, SecurityType.STOCK_ETF)
        self.assertEqual(info.period, Period.DAY)
        self.assertEqual(info.adjusted_close, True)

    def test_currency_usd__should_have_correct_fields(self):
        info = yapo.information('cbr/USD')
        self.assertEqual(info.namespace, 'cbr')
        self.assertEqual(info.ticker, 'USD')
        self.assertIsNone(info.isin)
        self.assertEqual(info.short_name, 'Доллар США')
        self.assertIsNone(info.long_name)
        self.assertIsNone(info.exchange)
        self.assertEqual(info.currency, Currency.USD)
        self.assertEqual(info.security_type, SecurityType.CURRENCY)
        self.assertEqual(info.period, Period.DAY)
        self.assertEqual(info.adjusted_close, True)

    def test_inflation_ru__should_have_correct_fields(self):
        info = yapo.information('infl/RU')
        self.assertEqual(info.namespace, 'infl')
        self.assertEqual(info.ticker, 'RU')
        self.assertIsNone(info.isin)
        self.assertEqual(info.short_name, 'Инфляция РФ')
        self.assertIsNone(info.long_name)
        self.assertIsNone(info.exchange)
        self.assertEqual(info.currency, Currency.RUB)
        self.assertEqual(info.security_type, SecurityType.INFLATION)
        self.assertEqual(info.period, Period.MONTH)
        self.assertEqual(info.adjusted_close, False)

    def test_all_data_should_be_available(self):
        self.assertIsNotNone(yapo.information('quandl/MSFT'))
        self.assertIsNotNone(yapo.information('micex/SBER'))
        self.assertIsNotNone(yapo.information('micex/SBERP'))
        self.assertIsNotNone(yapo.information('micex/MCFTR'))
        self.assertIsNotNone(yapo.information('nlu/419'))
        self.assertIsNotNone(yapo.information('cbr/USD'))
        self.assertIsNotNone(yapo.information('cbr/EUR'))
        self.assertIsNotNone(yapo.information('infl/RU'))
        self.assertIsNotNone(yapo.information('infl/US'))
        self.assertIsNotNone(yapo.information('infl/EU'))
        self.assertIsNotNone(yapo.information('cbr/TOP_rates'))

    def test_return_none_if_no_ticker_is_found(self):
        not_existing_id = 'micex/MCFTR_doesntexist'

        self.assertIsNone(yapo.information(not_existing_id))

        infos = yapo.information('infl/RU, {}'.format(not_existing_id))
        self.assertIsNotNone(infos[0])
        self.assertIsNone(infos[1])

    def test_return_same_infos_count_as_provided(self):
        ids_arr = ['infl/RU', 'infl/EU', 'micex/MCFTR', 'micex/SBER']
        infos = yapo.information(', '.join(ids_arr))
        self.assertEqual(len(infos), len(ids_arr))

    def test_be_invariant_in_respect_to_space_separators(self):
        infos1 = yapo.information('infl/RU, infl/EU')
        infos2 = yapo.information('    infl/RU    ,      infl/EU      ')
        self.assertCountEqual(infos1, infos2)

    def test_be_invariant_in_respect_to_order(self):
        infos1 = yapo.information('infl/RU, infl/EU')
        infos2 = yapo.information('infl/EU, infl/RU')
        self.assertCountEqual(infos1, infos2)