SCHEMA = """
create table competitors
(
    id                      int unsigned auto_increment comment '唯一标识符'
        primary key,
    competitor_name         varchar(50)   not null comment '竞品名称',
    car_series              varchar(50)   not null comment '车系名称',
    sales                   int           not null comment '竞品销量',
    market_share_percentage decimal(5, 2) not null comment '竞品市场占有率百分比',
    record_date             date          not null comment '记录日期'
)
    comment '存储竞品销量和市场占有率' collate = utf8mb4_unicode_520_ci;

create table customer_flow
(
    id               int unsigned auto_increment comment '唯一标识符'
        primary key,
    region           varchar(50)   not null comment '大区',
    store            varchar(50)   not null comment '门店名称',
    first_visit_flow int           not null comment '首次到店客流量',
    total_visit_flow int           not null comment '总客流量',
    visit_datetime   datetime      not null comment '访问时间',
    conversion_rate  decimal(5, 2) not null comment '成交率'
)
    comment '存储大区、门店、客流量和成交率信息' collate = utf8mb4_unicode_520_ci;

create index idx_region_store
    on customer_flow (region, store);

create table inventory
(
    id           int unsigned auto_increment comment '唯一标识符'
        primary key,
    car_series   varchar(50)  not null comment '车系名称',
    region       varchar(50)  not null comment '大区',
    warehouse    varchar(100) not null comment '仓库名称',
    quantity     int          not null comment '库存数量',
    last_checked datetime     not null comment '最后盘点时间',
    series_type  varchar(50)  not null comment '车系类型'
)
    comment '存储库存信息' collate = utf8mb4_unicode_520_ci;

create table market_sales
(
    id                      int unsigned auto_increment comment '唯一标识符'
        primary key,
    total_market_sales      int  not null comment '总体市场销量',
    car_series_market_sales int  not null comment '车系市场销量',
    record_date             date not null comment '记录日期'
)
    comment '存储市场销量信息' collate = utf8mb4_unicode_520_ci;

create table market_share
(
    id                      int unsigned auto_increment comment '唯一标识符'
        primary key,
    car_series              varchar(50)   not null comment '车系名称',
    market_share_percentage decimal(5, 2) not null comment '市场占有率百分比',
    record_date             date          not null comment '记录日期'
)
    comment '存储车系市场占有率变化' collate = utf8mb4_unicode_520_ci;

create table order_stats
(
    id                            int unsigned auto_increment comment '唯一标识符'
        primary key,
    car_series                    varchar(50) not null comment '车系名称',
    region                        varchar(50) not null comment '大区',
    order_quantity                int         not null comment '订单数量',
    large_order_quantity          int         not null comment '大定数量',
    locked_order_quantity         int         not null comment '锁单数量',
    retained_large_order_quantity int         not null comment '留存大定数量'
)
    comment '存储订单统计数据' collate = utf8mb4_unicode_520_ci;

create table policies
(
    id             int unsigned auto_increment comment '唯一标识符'
        primary key,
    policy_name    varchar(100) not null comment '政策名称',
    description    text         null comment '政策描述',
    type           varchar(50)  not null comment '车系类型',
    effective_date date         not null comment '生效日期',
    expiry_date    date         null comment '失效日期'
)
    comment '存储国家及地方汽车产业政策' collate = utf8mb4_unicode_520_ci;

create table sales
(
    id          int unsigned auto_increment comment '唯一标识符'
        primary key,
    car_series  varchar(50) not null comment '车系名称',
    region      varchar(50) not null comment '大区',
    quantity    int         not null comment '销量数量',
    sale_date   date        not null comment '销售日期',
    series_type varchar(50) not null comment '车系类型'
)
    comment '存储实际销量数据' collate = utf8mb4_unicode_520_ci;

create table sales_targets
(
    id             int unsigned auto_increment comment '唯一标识符'
        primary key,
    car_series     varchar(50) not null comment '车系名称',
    region         varchar(50) not null comment '大区',
    monthly_target int         not null comment '月度销量目标',
    yearly_target  int         not null comment '年度销量目标'
)
    comment '存储各车系在各大区的销量目标' collate = utf8mb4_unicode_520_ci;
"""