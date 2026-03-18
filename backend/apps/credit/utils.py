from decimal import Decimal, ROUND_HALF_UP


def mensualite(capital: Decimal, taux_annuel: Decimal, n_mois: int) -> Decimal:
    """
    Formule cahier des charges:
    Mensualité = Capital * (t/12) / (1 - (1 + t/12)^-n)
    où t est en décimal (ex: 0.033 pour 3.3%).
    """
    if n_mois <= 0:
        raise ValueError("n_mois doit être > 0")
    if capital <= 0:
        raise ValueError("capital doit être > 0")
    if taux_annuel < 0:
        raise ValueError("taux_annuel doit être >= 0")

    if taux_annuel == 0:
        m = capital / Decimal(n_mois)
        return m.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    t_m = taux_annuel / Decimal(12)
    denom = Decimal(1) - (Decimal(1) + t_m) ** Decimal(-n_mois)
    m = capital * t_m / denom
    return m.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def cout_total(mensualite_val: Decimal, n_mois: int, capital: Decimal) -> Decimal:
    total = (mensualite_val * Decimal(n_mois)) - capital
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def taux_endettement(charges: Decimal, revenus: Decimal) -> Decimal:
    if revenus <= 0:
        return Decimal("0.00")
    te = (charges / revenus) * Decimal(100)
    return te.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

