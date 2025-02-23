DROP TABLE IF EXISTS transactions_enhanced;

CREATE TABLE transactions_enhanced
USING DELTA
AS
  SELECT
    b.subscription_id,
    a.*,
    COALESCE( DATEDIFF(a.transaction_date, LAG(a.transaction_date, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date)), 0) as days_since_last_transaction,
    COALESCE( a.plan_list_price - LAG(a.plan_list_price, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date), 0) as change_in_list_price,
    COALESCE(a.actual_amount_paid - LAG(a.actual_amount_paid, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date), 0) as change_in_actual_amount_paid,
    COALESCE(a.discount - LAG(a.discount, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date), 0) as change_in_discount,
    COALESCE(a.payment_plan_days - LAG(a.payment_plan_days, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date), 0) as change_in_payment_plan_days,
    CASE WHEN (a.payment_method_id != LAG(a.payment_method_id, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date)) THEN 1 ELSE 0 END  as change_in_payment_method_id,
    CASE
      WHEN a.is_cancel = LAG(a.is_cancel, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date) THEN 0
      WHEN a.is_cancel = 0 THEN -1
      ELSE 1
      END as change_in_cancellation,
    CASE
      WHEN a.is_auto_renew = LAG(a.is_auto_renew, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date) THEN 0
      WHEN a.is_auto_renew = 0 THEN -1
      ELSE 1
      END as change_in_auto_renew,
    COALESCE( DATEDIFF(a.membership_expire_date, LAG(a.membership_expire_date, 1) OVER(PARTITION BY b.subscription_id ORDER BY a.transaction_date)), 0) as days_change_in_membership_expire_date

  FROM transactions_clean a
  INNER JOIN subscription_windows b
    ON a.msno=b.msno AND 
       a.transaction_date BETWEEN b.subscription_start AND b.subscription_end
  ORDER BY 
    a.msno,
    a.transaction_date;
    
SELECT * FROM transactions_enhanced;