


# דוח פרויקט בסיסי נתונים - שלב ב'

## אריאל נמיר 123456789
## זורנו אריאל 285495067
## אוריה שחור 309857569

## ## חלק א': שאילתות SELECT כפולות
## כול התמונות בסוף ובקובץ נפרד לצורך נוחות הקורא#

### שאילתה 1: מסך סקאוטינג (Scouting Screen)
**תיאור השאילתא:** שליפת השם הפרטי, שם המשפחה, המחיר ושנת הלידה של שחקנים שנולדו בשנת
## 2002 ומשחקים בקבוצות הממוקמות באנגליה.

**קוד השאילתא (Method A - שימוש בתנאי IN):**
```sql
SELECT p.first_name, p.last_name, p.price, EXTRACT(YEAR FROM p.birth_date) AS
birth_year
FROM PLAYER p
WHERE EXTRACT(YEAR FROM p.birth_date) = 2002
AND p.real_team_id IN (
SELECT real_team_id
## FROM REAL_TEAM
WHERE country = 'England'
 );
```



## **הסבר על ההבדלים ויעילות:**
## שיטה A משתמשת בתנאי `IN` המבצע בדיקת שייכות לקבוצת ערכים קבועה מראש החוזרת
מתת-השאילתה. במידה ושיטה B תמומש באמצעות `JOIN` מפורש, מנועי בסיסי נתונים מודרניים יבצעו
לרוב אופטימיזציה דומה )כמו Semi-Join). היתרון של שימוש ב-`IN` במקרה זה הוא מניעת שכפול שורות
בתוצאה הסופית במידה וישנן רשומות כפולות בטבלת היעד, והוא שומר על קריאות גבוהה של הקוד בהתאם
## ללוגיקה העסקית של המערכת.

## ---

### שאילתה 2: מסך מנהל (Admin Screen)

**תיאור השאילתא:** הצגת שמות קבוצות הפנטזי, התקציב שנותר להן ושם המשתמש, עבור קבוצות
שהתקציב הנותר שלהן גדול מהתקציב הממוצע של כלל הקבוצות המשתתפות בליגות שהחלו בחודש
## אוגוסט.



**קוד השאילתא (Method B - שימוש ב-Virtual Table / Derived Table):**

## ```sql

SELECT ft.team_name, ft.budget_remaining, u.username
FROM FANTASY_TEAM ft
JOIN USERS u ON ft.user_id = u.user_id
## JOIN (
SELECT AVG(budget_remaining) AS avg_budget
FROM FANTASY_TEAM ft_sub
JOIN FANTASY_LEAGUE fl_sub ON ft_sub.league_id = fl_sub.league_id
WHERE EXTRACT(MONTH FROM fl_sub.start_date) = 8
) avg_table ON ft.budget_remaining > avg_table.avg_budget
ORDER BY ft.budget_remaining DESC;
```


## **הסבר על ההבדלים ויעילות:**
שיטה B משתמשת בטבלה וירטואלית (Derived Table) המוגדרת בתוך תנאי ה-`FROM`. גישה זו יעילה
מאוד מכיוון שמנוע בסיס הנתונים מריץ את תת-השאילתה ומחשב את הערך הממוצע (AVG) פעם אחת
בלבד עבור כל הטרנזקציה, שומר את התוצאה בזיכרון הזמני, ואז משתמש בה לצורך ביצוע ה-`JOIN`.
לעומת זאת, שימוש בתת-שאילתה רגילה בתוך תנאי ה-`WHERE` (במיוחד אם היא Correlated) עלול
לגרום למנוע לחשב את הממוצע מחדש עבור כל שורה ושורה בטבלה הראשית, דבר המאט משמעותית את
## זמן הריצה בטבלאות גדולות.

## ---

### שאילתה 3: היסטוריית העברות (Transfer History)

**תיאור השאילתא:** מציאת שמות המשתמשים והאימיילים של מנהלים שמעולם לא ביצעו העברת שחקן
(Transfer) ביום הראשון של שום חודש.

**קוד השאילתא (Method A):**

**קוד השאילתא (Method B - שימוש ב-NOT EXISTS):**

## ```sql
SELECT u.username, u.email
FROM USERS u
## WHERE NOT EXISTS (
## SELECT 1
FROM TRANSFER t
JOIN FANTASY_TEAM ft ON t.team_id = ft.team_id
WHERE ft.user_id = u.user_id
AND EXTRACT(DAY FROM t.transfer_date) = 1
## );


## **הסבר על ההבדלים ויעילות:**
שיטה B עושה שימוש ב-`NOT EXISTS`, בעוד ששיטה חלופית (Method A) תשתמש לרוב ב-`NOT IN`.
מבחינת ביצועים, `NOT EXISTS` יעילה משמעותית משום שהיא משתמשת במנגנון עצירה מוקדמת
(Short-circuit evaluation) – ברגע שנמצאת רשומה אחת שעונה על התנאי בתת-השאילתה, הסריקה
עבור אותו משתמש נעצרת והוא מסונן החוצה. מעבר לכך, `NOT EXISTS` בטוחה ואמינה יותר לשימוש

בהקשר של ערכי `NULL`; אם תת-שאילתה המופעלת עם `NOT IN` תחזיר ולו ערך `NULL` אחד, כל
השאילתה כולה תיכשל ותחזיר אפס רשומות, בעוד ש-`NOT EXISTS` מתעלמת מערכים אלו ומחזירה
## תוצאות אמת.

## ---

### שאילתה 4: טבלת מובילים גלובלית (Global Leaderboard)

**תיאור השאילתא:** הצגת שמות הקבוצות, סך הנקודות ושם הליגה, עבור קבוצות שהשיגו מעל ל-50
## נקודות והשתתפו בליגות שהסתיימו בשנת 2024.

**קוד השאילתא (Method A - Explicit INNER JOIN):**

## ```sql
SELECT ft.team_name, ft.total_points, fl.league_name
FROM FANTASY_TEAM ft
JOIN FANTASY_LEAGUE fl ON ft.league_id = fl.league_id
WHERE ft.total_points > 50
AND EXTRACT(YEAR FROM fl.end_date) = 2024;

## ```

**קוד השאילתא (Method B - Implicit JOIN בתוך תנאי WHERE):**

## ```sql
SELECT ft.team_name, ft.total_points, fl.league_name
FROM FANTASY_TEAM ft, FANTASY_LEAGUE fl
WHERE ft.league_id = fl.league_id
AND ft.total_points > 50
AND EXTRACT(YEAR FROM fl.end_date) = 2024;

## ```

## **הסבר על ההבדלים ויעילות:**
שיטה A משתמשת בצירוף מפורש (`JOIN...ON`) התואם לתקן המודרני ANSI-92, ואילו שיטה B
משתמשת בצירוף מרומז (Implicit Join) על ידי הפרדת הטבלאות בפסיקים בתוך ה-`FROM` והגדרת
הקשר הלוגי בתוך ה-`WHERE` (תקן ישן ANSI-89). מבחינת ביצועי מנוע בסיס הנתונים וזמני ריצה, אין
הבדל בין השתיים, שכן האופטימייזר המודרני מתרגם את שתיהן לאותה תוכנית הרצה (Execution Plan).
עם זאת, שיטה A נחשבת ל-Best Practice מובהק משום שהיא מפרידה לחלוטין בין תנאי הקישור של
הטבלאות (ON) לבין תנאי הסינון של הרשומות (WHERE), מה שמונע שגיאות קריטיות של היווצרות
מכפלה קרטזית (Cross Join) בטעות ומקל על תחזוקת הקוד.

## ---

## ## חלק ב': 4 שאילתות SELECT נוספות

### שאילתה 5: קבוצת החודש (Team of the Month)


**תיאור השאילתא:** חישוב סך השערים שהובקעו לפי לאום של שחקנים במהלך חודש דצמבר, והצגת
## הלאומים שהבקיעו במצטבר מעל 10 שערים, ממוין בסדר יורד מהגבוה לנמוך.

## **קוד השאילתא:**

## ```sql
SELECT p.nationality, SUM(pgs.goals_scored) AS total_goals_december,
COUNT(p.player_id) AS players_involved
FROM PLAYER p
JOIN PLAYER_GAMEWEEK_STATS pgs ON p.player_id = pgs.player_id
JOIN MATCH m ON pgs.match_id = m.match_id
WHERE EXTRACT(MONTH FROM m.match_date) = 12
GROUP BY p.nationality
HAVING SUM(pgs.goals_scored) > 10
ORDER BY total_goals_december DESC;

## ```
## ---

### שאילתה 6: אנליטיקת משתמשים (User Analytics)

**תיאור השאילתא:** חישוב סך ההוצאות על העברות שחקנים (Transfers) שבוצעו על ידי משתמשים
שנרשמו למערכת במהלך שנת 2023, מקובץ לפי שם המשתמש וחודש הרישום, וממוין מההוצאה הגבוהה
## לנמוכה.

## **קוד השאילתא:**

## ```sql
SELECT u.username, EXTRACT(MONTH FROM u.registration_date) AS reg_month,
SUM(t.price_paid) AS total_spent_on_transfers
FROM USERS u
JOIN FANTASY_TEAM ft ON u.user_id = ft.user_id
JOIN TRANSFER t ON ft.team_id = t.team_id
WHERE EXTRACT(YEAR FROM u.registration_date) = 2023
GROUP BY u.username, u.registration_date
ORDER BY total_spent_on_transfers DESC;

## ```
## ---

### שאילתה 7: טבלת ליגה בזמן אמת (Live League Table)

**תיאור השאילתא:** שליפת הדירוג, שם הקבוצה, שם המשתמש והנקודות עבור ליגה מספר 1, מוגבל
למחזורים (Gameweeks) שהחלו בין היום ה-1 ליום ה-15 של החודש, מסודר בסדר עולה לפי מיקום
## הקבוצה בטבלה.

## **קוד השאילתא:**


## ```sql
SELECT ls.rank, ft.team_name, u.username, ls.points, EXTRACT(DAY FROM
gw.start_date) AS gw_start_day
FROM LEAGUE_STANDING ls
JOIN FANTASY_TEAM ft ON ls.team_id = ft.team_id
JOIN USERS u ON ft.user_id = u.user_id
JOIN GAMEWEEK gw ON ls.gameweek_id = gw.gameweek_id
WHERE ls.league_id = 1
AND EXTRACT(DAY FROM gw.start_date) BETWEEN 1 AND 15
ORDER BY ls.rank ASC;

## ```
## ---

### שאילתה 8: נתוני מועדונים אמיתיים (Real Club Stats)

**תיאור השאילתא:** ספירת כמות השחקנים הכוללת ומציאת מחיר השחקן היקר ביותר עבור כל מועדון
## כדורגל אמיתי שהוקם לפני שנת 1900, ממוין מהשחקן היקר ביותר ומטה.

## **קוד השאילתא:**

## ```sql
SELECT rt.team_name, rt.founded_year, COUNT(p.player_id) AS num_of_players,
MAX(p.price) AS most_expensive_player
FROM REAL_TEAM rt
JOIN PLAYER p ON rt.real_team_id = p.real_team_id
WHERE rt.founded_year < 1900
GROUP BY rt.team_name, rt.founded_year
ORDER BY most_expensive_player DESC;

## ```
## ---

## ## חלק ג': שאילתות UPDATE ו-DELETE

## ### עדכון 1: Dynamic Price Update

**תיאור השאילתא:** עדכון מחיר דינמי - העלאת מחיר השחקן ב-0.5 עבור שחקנים שנבחרו כקפטן ביותר
## מ-100 קבוצות פנטזי שונות במערכת.

## **קוד השאילתא:**

## ```sql
## UPDATE PLAYER
SET price = price + 0.5
WHERE player_id IN (
SELECT player_id
## FROM FANTASY_TEAM_SELECTION

WHERE is_captain = 1
GROUP BY player_id
## HAVING COUNT(*) > 100
## );

## ---

## ### עדכון 2: Budget Penalty

**תיאור השאילתא:** קנס נקודות - הפחתת 5 נקודות מסך הנקודות הכללי של קבוצות פנטזי אשר חרגו
## והוציאו סכום מצטבר הגבוה מ-10.0 על העברות שחקנים במהלך חודש ינואר.

## **קוד השאילתא:**

## ```sql
## UPDATE FANTASY_TEAM
SET total_points = total_points - 5
WHERE team_id IN (
SELECT t.team_id
FROM TRANSFER t
WHERE EXTRACT(MONTH FROM t.transfer_date) = 1
GROUP BY t.team_id
HAVING SUM(t.price_paid) > 10.0
## );

## ```
## ---

## ### עדכון 3: Auto Status Update

**תיאור השאילתא:** עדכון סטטוס אוטומטי - שינוי סטטוס המשחק ל"הסתיים" (status_id = 3) עבור כל
## המשחקים שהתקיימו בשנת 2023 ותאריכם ההיסטורי קטן מהתאריך הנוכחי.

## **קוד השאילתא:**

## ```sql
## UPDATE MATCH
SET status_id = 3
WHERE match_date < CURRENT_DATE
AND EXTRACT(YEAR FROM match_date) = 2023;

## ```
## ---

## ### מחיקה 1: Clean Ghost Teams

**תיאור השאילתא:** ניקוי קבוצות רפאים - מחיקת קבוצות פנטזי השייכות למשתמשים ישנים שנרשמו לפני
## שנת 2020, בתנאי שהקבוצות הללו מעולם לא ביצעו בחירת סגל שחקנים בפועל.


## **קוד השאילתא:**

## ```sql
## DELETE FROM FANTASY_TEAM
WHERE user_id IN (
SELECT user_id FROM USERS WHERE EXTRACT(YEAR FROM registration_date) <
## 2020
## )
AND team_id NOT IN (
SELECT DISTINCT team_id FROM FANTASY_TEAM_SELECTION
## );

## ```
## ---

### מחיקה 2: Remove Selections for Cancelled Matches

**תיאור השאילתא:** הסרת בחירות ממשחקים מבוטלים - מחיקת רשומות בחירת שחקנים מסגלי הפנטזי
## עבור שחקנים ומחזורי משחק שבהם המשחק האמיתי בוטל )סטטוס משחק מוגדר כ-5).

## **קוד השאילתא:**

## ```sql
## DELETE FROM FANTASY_TEAM_SELECTION
WHERE (player_id, gameweek_id) IN (
SELECT pgs.player_id, pgs.gameweek_id
FROM PLAYER_GAMEWEEK_STATS pgs
JOIN MATCH m ON pgs.match_id = m.match_id
WHERE m.status_id = 5
## );

## ```
## ---

## ### מחיקה 3: Transfer History Archive

**תיאור השאילתא:** ארכוב היסטוריית העברות - מחיקת רשומות היסטוריות מטבלת ההעברות
(Transfers) עבור קבוצות ששיחקו בליגות שהסתיימו לפני שנת 2023, לצורך פינוי מקום וייעול נפח בסיס
## הנתונים.

## **קוד השאילתא:**

## ```sql
## DELETE FROM TRANSFER
WHERE team_id IN (
SELECT ft.team_id
FROM FANTASY_TEAM ft

JOIN FANTASY_LEAGUE fl ON ft.league_id = fl.league_id
WHERE EXTRACT(YEAR FROM fl.end_date) < 2023
## );

## ```

## ---

## חלק ד': אילוצים (Constraints)

## ### אילוץ 1: [...]

## **תיאור השינוי בעזרת פקודת ALTER TABLE:**

## * **ניסיון הכנסת נתונים הסותרים את האילוץ:**

## ---

## חלק ה': טרנזקציות (Commit ו-Rollback)

## ### דוגמה 1: ביצוע Commit (שמירת שינויים)

## **קוד הטרנזקציה:**



## ### דוגמה 2: ביצוע Rollback (ביטול שינויים)

## **קוד הטרנזקציה:**


## ## חלק ו': אינדקסים וזמני ריצה

## ### אינדקס 1: [...]

## **פקודת יצירת האינדקס:**
## **הסבר התוצאות:**

## ```

## ```




































<img width="1146" height="456" alt="image (6)" src="https://github.com/user-attachments/assets/41eb4d02-ce3c-488b-9e3a-9905bc1158ef" />
<img width="1414" height="830" alt="image (5)" src="https://github.com/user-attachments/assets/f61da0b4-7597-4f10-acb7-c15f17feac55" />
<img width="1780" height="980" alt="image (4)" src="https://github.com/user-attachments/assets/41c05495-1475-486a-9546-571fb6c25934" />
<img width="1782" height="982" alt="image (3)" src="https://github.com/user-attachments/assets/55f8c165-dfd0-4d43-ae90-10144302b410" />
<img width="1822" height="1002" alt="image (2)" src="https://github.com/user-attachments/assets/4dc29ce4-6af9-435b-a884-d18146e1aaae" />

































