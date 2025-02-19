DROP TABLE IF EXISTS subscription_windows;

CREATE TABLE subscription_windows 
USING delta
AS
  WITH end_dates (
      SELECT p.*
      FROM (
        SELECT
          m.msno,
          m.transaction_date,
          m.membership_expire_date,
          m.next_transaction_date,
          CASE
            WHEN m.next_transaction_date IS NULL THEN 1
            WHEN DATEDIFF(m.next_transaction_date, m.membership_expire_date) > 30 THEN 1
            ELSE 0
            END as end_flag,
          CASE
            WHEN m.next_transaction_date IS NULL THEN m.membership_expire_date
            WHEN DATEDIFF(m.next_transaction_date, m.membership_expire_date) > 30 THEN m.membership_expire_date
            ELSE DATE_ADD(m.next_transaction_date, -1)  -- then just move the needle to just prior to the next transaction
            END as end_date
        FROM (
          SELECT
            x.msno,
            x.transaction_date,
            CASE  -- correct backdated expirations for subscription end calculations
              WHEN x.membership_expire_date < x.transaction_date THEN x.transaction_date
              ELSE x.membership_expire_date
              END as membership_expire_date,
            LEAD(x.transaction_date, 1) OVER (PARTITION BY x.msno ORDER BY x.transaction_date) as next_transaction_date
          FROM transactions_clean x
          ) m
        ) p
      WHERE p.end_flag=1
    )
  SELECT
    ROW_NUMBER() OVER (ORDER BY subscription_start, msno) as subscription_id,
    msno,
    subscription_start,
    subscription_end
  FROM (
    SELECT
      x.msno,
      MIN(x.transaction_date) as subscription_start,
      y.window_end as subscription_end
    FROM transactions_clean x
    INNER JOIN (
      SELECT
        a.msno,
        COALESCE( MAX(b.end_date), '2015-01-01') as window_start,
        a.end_date as window_end
      FROM end_dates a
      LEFT OUTER JOIN end_dates b
        ON a.msno=b.msno AND a.end_date > b.end_date
      GROUP BY a.msno, a.end_date
      ) y
      ON x.msno=y.msno AND x.transaction_date BETWEEN y.window_start AND y.window_end
    GROUP BY x.msno, y.window_end
    )
  ORDER BY subscription_id;
  
SELECT *
FROM subscription_windows
ORDER BY subscription_id;