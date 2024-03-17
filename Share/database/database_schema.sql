-- 原始相关数据表
CREATE TABLE "hh_quant_stock_trade_date_info" (
    datetime DATE NOT NULL PRIMARY KEY
);

CREATE TABLE "hh_quant_stock_base_info" (
    stock_code TEXT NOT NULL PRIMARY KEY
  , stock_name TEXT
  , stock_prefix TEXT
);

CREATE TABLE "hh_quant_stock_history_info" (
    stock_code TEXT NOT NULL
  , adjust_type TEXT
  , datetime DATE NOT NULL
  , open REAL
  , high REAL
  , low REAL
  , close REAL
  , volume REAL
  , amount REAL
  , turnover_rate REAL
  , PRIMARY KEY(stock_code, datetime)
);

CREATE TABLE "hh_quant_stock_individual_info" (
    stock_code TEXT NOT NULL PRIMARY KEY
  , stock_name TEXT
  , total_market_cap REAL
  , circulating_market_cap REAL
  , industry TEXT
  , listing_date INTEGER
  , total_shares REAL
  , circulating_shares REAL
);

CREATE TABLE "hh_quant_stock_indicator_info" (
    stock_code TEXT NOT NULL
  , datetime DATE NOT NULL
  , pe_ttm REAL
  , ps_ttm REAL
  , pcf_ncf_ttm REAL
  , pb_mrq REAL
  , PRIMARY KEY(stock_code, datetime)
);

-- CREATE TABLE "hh_quant_index_base_info" (
--     index_code TEXT NOT NULL PRIMARY KEY
--   , index_name TEXT
--   , publish_date DATE
-- );

CREATE TABLE "hh_quant_index_history_info" (
    index_code TEXT NOT NULL
  , datetime DATE NOT NULL
  , open REAL
  , high REAL
  , low REAL
  , close REAL
  , volume REAL
  , amount REAL
  , PRIMARY KEY(index_code, datetime)
);

-- Factor相关数据表
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
    , KMID REAL
    , KLEN REAL
    , KMID2 REAL
    , KUP REAL
    , KUP2 REAL
    , KLOW REAL
    , KLOW2 REAL
    , KSFT REAL
    , KSFT2 REAL
    , OPEN0 REAL
    , OPEN1 REAL
    , OPEN2 REAL
    , OPEN3 REAL
    , OPEN4 REAL
    , HIGH0 REAL
    , HIGH1 REAL
    , HIGH2 REAL
    , HIGH3 REAL
    , HIGH4 REAL
    , LOW0 REAL
    , LOW1 REAL
    , LOW2 REAL
    , LOW3 REAL
    , LOW4 REAL
    , CLOSE0 REAL
    , CLOSE1 REAL
    , CLOSE2 REAL
    , CLOSE3 REAL
    , CLOSE4 REAL
    , VOLUME0 REAL
    , VOLUME1 REAL
    , VOLUME2 REAL
    , VOLUME3 REAL
    , VOLUME4 REAL
    , ROC5 REAL
    , ROC10 REAL
    , ROC20 REAL
    , ROC30 REAL
    , ROC60 REAL
    , MAX5 REAL
    , MAX10 REAL
    , MAX20 REAL
    , MAX30 REAL
    , MAX60 REAL
    , MIN5 REAL
    , MIN10 REAL
    , MIN20 REAL
    , MIN30 REAL
    , MIN60 REAL
    , MA5 REAL
    , MA10 REAL
    , MA20 REAL
    , MA30 REAL
    , MA60 REAL
    , STD5 REAL
    , STD10 REAL
    , STD20 REAL
    , STD30 REAL
    , STD60 REAL
    , BETA5 REAL
    , BETA10 REAL
    , BETA20 REAL
    , BETA30 REAL
    , BETA60 REAL
    , RSQR5 REAL
    , RSQR10 REAL
    , RSQR20 REAL
    , RSQR30 REAL
    , RSQR60 REAL
    , RESI5 REAL
    , RESI10 REAL
    , RESI20 REAL
    , RESI30 REAL
    , RESI60 REAL
    , QTLU5 REAL
    , QTLU10 REAL
    , QTLU20 REAL
    , QTLU30 REAL
    , QTLU60 REAL
    , QTLD5 REAL
    , QTLD10 REAL
    , QTLD20 REAL
    , QTLD30 REAL
    , QTLD60 REAL
    , TSRANK5 REAL
    , TSRANK10 REAL
    , TSRANK20 REAL
    , TSRANK30 REAL
    , TSRANK60 REAL
    , RSV5 REAL
    , RSV10 REAL
    , RSV20 REAL
    , RSV30 REAL
    , RSV60 REAL
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
    , VMA5 REAL
    , VMA10 REAL
    , VMA20 REAL
    , VMA30 REAL
    , VMA60 REAL
    , VSTD5 REAL
    , VSTD10 REAL
    , VSTD20 REAL
    , VSTD30 REAL
    , VSTD60 REAL
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