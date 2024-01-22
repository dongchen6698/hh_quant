CREATE TABLE "hh_quant_stock_trade_date_info" (
    datetime DATE NOT NULL PRIMARY KEY
);

CREATE TABLE "hh_quant_stock_base_info" (
    stock_code TEXT NOT NULL PRIMARY KEY
  , stock_name TEXT
);

CREATE TABLE "hh_quant_stock_history_info" (
    stock_code TEXT NOT NULL
  , stock_name TEXT
  , stock_adjust TEXT
  , datetime DATE NOT NULL
  , open REAL
  , close REAL
  , high REAL
  , low REAL
  , volume INTEGER
  , turnover REAL
  , amplitude REAL
  , change_pct REAL
  , change_amount REAL
  , turnover_rate REAL
  , PRIMARY KEY(stock_code, datetime)
);


CREATE TABLE "hh_quant_stock_individual_info" (
    total_market_cap REAL
  , circulating_market_cap REAL
  , industry TEXT
  , listing_date INTEGER
  , stock_code TEXT NOT NULL PRIMARY KEY
  , stock_name TEXT
  , total_shares REAL
  , circulating_shares REAL
);


CREATE TABLE "hh_quant_stock_event_info" (
    stock_code TEXT NOT NULL
  , stock_name TEXT
  , datetime DATE NOT NULL
  , event_type TEXT
  , event_content TEXT
  , PRIMARY KEY(stock_code, datetime)
);