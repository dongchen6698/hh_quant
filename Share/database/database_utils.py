def get_stock_code_prefix(stock_code):
    stock_code_starter = str(stock_code)[0]
    if stock_code_starter in ("4", "8"):
        return "bj"
    elif stock_code_starter in ("6"):
        return "sh"
    else:
        return "sz"
