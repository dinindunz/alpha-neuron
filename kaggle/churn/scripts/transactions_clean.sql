DROP TABLE IF EXISTS transactions_clean;

CREATE TABLE transactions_clean
USING DELTA
AS
  WITH 
    transaction_sequenced (
      SELECT
        msno,
        transaction_date,
        plan_list_price,
        payment_plan_days,
        payment_method_id,
        is_cancel,
        membership_expire_date,
        RANK() OVER (PARTITION BY msno, transaction_date ORDER BY plan_sort DESC, is_cancel) as sort_id  -- calc rank on price, days & method sort followed by cancel sort
      FROM (
        SELECT
          msno,
          transaction_date,
          plan_list_price,
          payment_plan_days,
          payment_method_id,
          CONCAT(CAST(plan_list_price as string), CAST(payment_plan_days as string), CAST(payment_method_id as string)) as plan_sort,
          is_cancel,
          membership_expire_date
        FROM transactions
        )
      )
  SELECT
    p.msno,
    p.transaction_date,
    p.plan_list_price,
    p.actual_amount_paid,
    p.plan_list_price - p.actual_amount_paid as discount,
    p.payment_plan_days,
    p.payment_method_id,
    p.is_cancel,
    p.is_auto_renew,
    p.membership_expire_date
  FROM transactions p
  INNER JOIN (
    SELECT
      x.msno,
      x.transaction_date,
      x.plan_list_price,
      x.payment_plan_days,
      x.payment_method_id,
      x.is_cancel,
      CASE   -- if is_cancel is 0 in last record then go with max membership date identified, otherwise go with lowest membership date
        WHEN x.is_cancel=0 THEN MAX(x.membership_expire_date)
        ELSE MIN(x.membership_expire_date)
        END as membership_expire_date
    FROM (
      SELECT
        a.msno,
        a.transaction_date,
        a.plan_list_price,
        a.payment_plan_days,
        a.payment_method_id,
        a.is_cancel,
        a.membership_expire_date
      FROM transaction_sequenced a
      INNER JOIN (
        SELECT msno, transaction_date, MAX(sort_id) as max_sort_id -- find last entries on a given date
        FROM transaction_sequenced 
        GROUP BY msno, transaction_date
        ) b
        ON a.msno=b.msno AND a.transaction_date=b.transaction_date AND a.sort_id=b.max_sort_id
        ) x
    GROUP BY 
      x.msno, 
      x.transaction_date, 
      x.plan_list_price,
      x.payment_plan_days,
      x.payment_method_id,
      x.is_cancel
   ) q
   ON 
     p.msno=q.msno AND 
     p.transaction_date=q.transaction_date AND 
     p.plan_list_price=q.plan_list_price AND 
     p.payment_plan_days=q.payment_plan_days AND 
     p.payment_method_id=q.payment_method_id AND 
     p.is_cancel=q.is_cancel AND 
     p.membership_expire_date=q.membership_expire_date;
     
SELECT * 
FROM transactions_clean
ORDER BY msno, transaction_date;