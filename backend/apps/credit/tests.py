from decimal import Decimal
from django.test import TestCase

from .utils import mensualite, cout_total, taux_endettement


class CreditUtilsTests(TestCase):
    def test_taux_endettement(self):
        self.assertEqual(taux_endettement(Decimal("900"), Decimal("3000")), Decimal("30.00"))

    def test_mensualite_taux_zero(self):
        m = mensualite(capital=Decimal("1200"), taux_annuel=Decimal("0"), n_mois=12)
        self.assertEqual(m, Decimal("100.00"))

    def test_mensualite_positive(self):
        m = mensualite(capital=Decimal("250000"), taux_annuel=Decimal("0.0331"), n_mois=240)
        self.assertTrue(m > 0)
        ct = cout_total(m, 240, Decimal("250000"))
        self.assertTrue(ct >= 0)

