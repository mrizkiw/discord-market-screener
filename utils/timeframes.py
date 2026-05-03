def get_mtf_mapping(main_tf: str):
    """Returns (macro_tf, micro_tf) for a given main timeframe."""
    mapping = {
        '1m': ('5m', None),
        '3m': ('15m', '1m'),
        '5m': ('15m', '1m'),
        '15m': ('1h', '5m'),
        '30m': ('4h', '5m'),
        '1h': ('4h', '15m'),
        '2h': ('1d', '30m'),
        '4h': ('1d', '1h'),
        '6h': ('1d', '1h'),
        '8h': ('1d', '2h'),
        '12h': ('3d', '4h'),
        '1d': ('1w', '4h'),
        '3d': ('1w', '1d'),
        '1w': ('1M', '1d'),
    }
    return mapping.get(main_tf.lower(), (None, None))
