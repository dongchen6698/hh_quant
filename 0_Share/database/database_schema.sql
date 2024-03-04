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

CREATE TABLE "hh_quant_stock_indicator_info" (
    stock_code TEXT NOT NULL
  , stock_name TEXT
  , datetime DATE NOT NULL
  , pe REAL
  , pe_ttm REAL
  , pb REAL
  , ps REAL
  , ps_ttm INTEGER
  , dv_ratio REAL
  , dv_ttm REAL
  , total_mv REAL
  , PRIMARY KEY(stock_code, datetime)
);

CREATE TABLE "hh_quant_index_base_info" (
    index_code TEXT NOT NULL PRIMARY KEY
  , index_name TEXT
  , publish_date DATE
);

CREATE TABLE "hh_quant_index_history_info" (
    index_code TEXT NOT NULL
  , index_name TEXT
  , index_publish_date DATE
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
  , PRIMARY KEY(index_code, datetime)
);

-- CREATE TABLE "hh_quant_stock_event_info" (
--     stock_code TEXT NOT NULL
--   , stock_name TEXT
--   , datetime DATE NOT NULL
--   , event_type TEXT
--   , event_content TEXT
--   , PRIMARY KEY(stock_code, datetime)
-- );

CREATE TABLE "hh_quant_stock_factor_date_info" (
    datetime DATE NOT NULL PRIMARY KEY
    , weekday INTEGER
    , day_of_week TEXT
    , day_of_month INTEGER
    , month INTEGER
    , season TEXT
);

CREATE TABLE hh_quant_stock_factor_qlib_info (
    stock_code TEXT NOT NULL
    , datetime DATE NOT NULL
    , KMID TEXT
    , KLEN TEXT
    , KMID2 TEXT
    , KUP TEXT
    , KUP2 TEXT
    , KLOW TEXT
    , KLOW2 TEXT
    , KSFT TEXT
    , KSFT2 TEXT
    , OPEN0 TEXT
    , OPEN1 TEXT
    , OPEN2 TEXT
    , OPEN3 TEXT
    , OPEN4 TEXT
    , HIGH0 TEXT
    , HIGH1 TEXT
    , HIGH2 TEXT
    , HIGH3 TEXT
    , HIGH4 TEXT
    , LOW0 TEXT
    , LOW1 TEXT
    , LOW2 TEXT
    , LOW3 TEXT
    , LOW4 TEXT
    , CLOSE0 TEXT
    , CLOSE1 TEXT
    , CLOSE2 TEXT
    , CLOSE3 TEXT
    , CLOSE4 TEXT
    , VOLUME0 TEXT
    , VOLUME1 TEXT
    , VOLUME2 TEXT
    , VOLUME3 TEXT
    , VOLUME4 TEXT
    , ROC5 TEXT
    , ROC10 TEXT
    , ROC20 TEXT
    , ROC30 TEXT
    , ROC60 TEXT
    , MAX5 TEXT
    , MAX10 TEXT
    , MAX20 TEXT
    , MAX30 TEXT
    , MAX60 TEXT
    , MIN5 TEXT
    , MIN10 TEXT
    , MIN20 TEXT
    , MIN30 TEXT
    , MIN60 TEXT
    , MA5 TEXT
    , MA10 TEXT
    , MA20 TEXT
    , MA30 TEXT
    , MA60 TEXT
    , STD5 TEXT
    , STD10 TEXT
    , STD20 TEXT
    , STD30 TEXT
    , STD60 TEXT
    , BETA5 TEXT
    , BETA10 TEXT
    , BETA20 TEXT
    , BETA30 TEXT
    , BETA60 TEXT
    , RSQR5 REAL
    , RSQR10 REAL
    , RSQR20 REAL
    , RSQR30 REAL
    , RSQR60 REAL
    , RESI5 TEXT
    , RESI10 TEXT
    , RESI20 TEXT
    , RESI30 TEXT
    , RESI60 TEXT
    , QTLU5 TEXT
    , QTLU10 TEXT
    , QTLU20 TEXT
    , QTLU30 TEXT
    , QTLU60 TEXT
    , QTLD5 TEXT
    , QTLD10 TEXT
    , QTLD20 TEXT
    , QTLD30 TEXT
    , QTLD60 TEXT
    , TSRANK5 REAL
    , TSRANK10 REAL
    , TSRANK20 REAL
    , TSRANK30 REAL
    , TSRANK60 REAL
    , RSV5 TEXT
    , RSV10 TEXT
    , RSV20 TEXT
    , RSV30 TEXT
    , RSV60 TEXT
    , IMAX5 REAL
    , IMAX10 REAL
    , IMAX20 REAL
    , IMAX30 REAL
    , IMAX60 REAL
    , IMIN5 REAL
    , IMIN10 REAL
    , IMIN20 REAL
    , IMIN30 REAL
    , IMIN60 REAL
    , IMXD5 REAL
    , IMXD10 REAL
    , IMXD20 REAL
    , IMXD30 REAL
    , IMXD60 REAL
    , CORR5 REAL
    , CORR10 REAL
    , CORR20 REAL
    , CORR30 REAL
    , CORR60 REAL
    , CORD5 REAL
    , CORD10 REAL
    , CORD20 REAL
    , CORD30 REAL
    , CORD60 REAL
    , CNTP5 REAL
    , CNTP10 REAL
    , CNTP20 REAL
    , CNTP30 REAL
    , CNTP60 REAL
    , CNTN5 REAL
    , CNTN10 REAL
    , CNTN20 REAL
    , CNTN30 REAL
    , CNTN60 REAL
    , CNTD5 REAL
    , CNTD10 REAL
    , CNTD20 REAL
    , CNTD30 REAL
    , CNTD60 REAL
    , SUMP5 REAL
    , SUMP10 REAL
    , SUMP20 REAL
    , SUMP30 REAL
    , SUMP60 REAL
    , SUMN5 REAL
    , SUMN10 REAL
    , SUMN20 REAL
    , SUMN30 REAL
    , SUMN60 REAL
    , SUMD5 REAL
    , SUMD10 REAL
    , SUMD20 REAL
    , SUMD30 REAL
    , SUMD60 REAL
    , VMA5 TEXT
    , VMA10 TEXT
    , VMA20 TEXT
    , VMA30 TEXT
    , VMA60 TEXT
    , VSTD5 TEXT
    , VSTD10 TEXT
    , VSTD20 TEXT
    , VSTD30 TEXT
    , VSTD60 TEXT
    , WVMA5 REAL
    , WVMA10 REAL
    , WVMA20 REAL
    , WVMA30 REAL
    , WVMA60 REAL
    , VSUMP5 REAL
    , VSUMP10 REAL
    , VSUMP20 REAL
    , VSUMP30 REAL
    , VSUMP60 REAL
    , VSUMN5 REAL
    , VSUMN10 REAL
    , VSUMN20 REAL
    , VSUMN30 REAL
    , VSUMN60 REAL
    , VSUMD5 REAL
    , VSUMD10 REAL
    , VSUMD20 REAL
    , VSUMD30 REAL
    , VSUMD60 REAL
    , PRIMARY KEY(stock_code, datetime)
  )