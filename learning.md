Concept: db.commit()
Purpose: Database transaction ko commit karke changes save karna.
Location: User create karte waqt database operation ke baad.
Example:
db.add(new_user)
db.commit()



# SkillBridge Project — Learning Notes

## 1. Project ka basic structure

Hum SkillBridge ko Python, FastAPI aur PostgreSQL ki help se bana rahe hain.

| File | Purpose |
|---|---|
| `main.py` | API endpoints banana aur request handle karna |
| `schemas.py` | Request data ki validation karna |
| `models.py` | Database tables aur columns define karna |
| `database.py` | Database connection aur session manage karna |
| `create_tables.py` | Database mein tables create karna |
| `.env` | Database URL jaise configuration aur secret values rakhna |
| `test_insert.py` | Testing ke liye database mein sample user insert karna |

**Yaad rakhne ka tarika:**
- `main.py` = API kya karegi?
- `schemas.py` = API ko kis type ka data chahiye?
- `models.py` = Database mein data ka structure kya hoga?
- `database.py` = Database se connection kaise hoga?
- PostgreSQL = Actual data kahan store hoga?

---

## 2. Database aur SQLAlchemy

SQLAlchemy Python code ki help se database ke saath kaam karne deta hai.

### Important concepts

- `engine`: Database connection manage karta hai.
- `SessionLocal`: Database session banane ke liye use hota hai.
- `Base`: SQLAlchemy models ko register karne mein help karta hai.
- `db.add()`: Naya object session mein add karta hai.
- `db.commit()`: Database changes save karta hai.
- `db.refresh()`: Database se object ki updated values laata hai.
- `db.rollback()`: Transaction fail hone par pending changes ko undo karta hai.
- `db.close()`: Database session close karta hai.

### Database session ka basic flow

1. Session create karo.
2. Database operation perform karo.
3. Changes ke liye `commit()` karo.
4. Error aaye toh zaroorat ke hisaab se `rollback()` karo.
5. Kaam khatam hone par session close karo.

FastAPI mein `get_db()` function aur `Depends(get_db)` ki help se endpoint ko database session diya ja sakta hai.

---

## 3. Model aur Schema mein difference

### Model — `models.py`

Model database table ka structure define karta hai.

Hamare `User` model mein:
- `id`: User ki unique identity.
- `name`: User ka naam.
- `email`: User ka unique email.
- `password_hash`: Password ka hashed version.
- `role`: User ka role, jaise student.

### Schema — `schemas.py`

Schema API ke through aane wale data ka format aur validation define karti hai.

Hamare `UserCreate` schema mein:
- `name`: Required, 2–100 characters.
- `email`: Valid email format hona chahiye.
- `password`: 8–128 characters.

**Important:** Model database ka structure define karta hai; schema input validation ke liye hoti hai. Dono ka purpose alag hai.

---

## 4. FastAPI endpoint kya hota hai?

Endpoint API ka ek address hota hai jahan client request bhejta hai.

Examples:
- `GET /health`: Application ka health status check karna.
- `GET /test-db`: Database connection test karna.
- `POST /register`: Naya user register karna.
- `PATCH /users/5`: ID 5 wale user ka kuch data update karna.

### Common HTTP methods

| Method | General purpose |
|---|---|
| `GET` | Data read karna |
| `POST` | Naya resource create karna |
| `PATCH` | Existing resource ka kuch data update karna |
| `PUT` | Aam taur par resource ko replace/update karna |
| `DELETE` | Resource delete karna |

---

## 5. User registration ka flow

Hamne `POST /register` endpoint banaya.

Iska basic flow:

1. User name, email aur password bhejta hai.
2. `UserCreate` schema input validate karti hai.
3. Database mein check hota hai ki email pehle se registered toh nahi.
4. `PasswordHash` se password ka hash banaya jaata hai.
5. User ka record database mein add hota hai.
6. `commit()` se record save hota hai.
7. Success response return hota hai.

**Security note:** Password ko plain text mein database mein store nahi karna chahiye. Hashed password store kiya jaata hai.

Registration mein duplicate email milne par hamara endpoint `409 Conflict` response deta hai.

---

## 6. PATCH aur partial update

PATCH tab use karte hain jab existing record ke selected fields update karne hon.

Example: Priya Sharma apna naam Priya Verma karna chahti hai.

Request:

`PATCH /users/5`

Request body:

```json
{
  "name": "Priya Verma"
}
```

Is request mein:
- Sirf `name` bheja gaya hai.
- Name update hoga.
- Email aur role jaise baaki fields unchanged rahenge.

### `UserCreate` aur `UserUpdate` alag kyun?

`UserCreate` naya account banane ke liye hai. Ismein required fields honi chahiye.

`UserUpdate` existing account ke selected fields update karne ke liye hai. Ismein update hone wale fields individually optional ho sakte hain.

Isliye hum `schemas.py` mein alag `UserUpdate` schema banayenge.

---

## 7. Optional fields aur empty request

Maan lo `UserUpdate` mein `name` aur `email` dono optional hain.

Valid partial update examples:

```json
{
  "name": "Priya Verma"
}
```

```json
{
  "email": "priya.new@example.com"
}
```

Lekin empty request:

```json
{}
```

Basic schema validation mein empty request valid ho sakti hai, agar dono fields optional hain.

Lekin hamari API mein business rule hona chahiye ki **kam se kam ek field update ke liye di jaaye**.

Agar koi field nahi aayi, toh request reject karni chahiye, kyunki update karne ke liye kuch hai hi nahi.

### Do alag concepts

- Schema validation: Har field ka data sahi hai ya nahi?
- Business validation: Request kaam karne ke liye logically valid hai ya nahi?

---

## 8. User ki ID se record identify karna

Example:

`PATCH /users/5`

Yahan `5` user ki ID hai.

Endpoint ko:
1. ID se user find karna hoga.
2. User nahi mila toh `404 Not Found` return karna hoga.
3. User mila toh requested fields update karni hongi.
4. Changes commit karke response dena hoga.

**Security note:** Real application mein sirf ID milna enough nahi hai. Authentication aur permission bhi check karni hogi, taaki student kisi doosre student ka data update na kar sake.

---

## 9. Naya feature khud se kaise plan karein?

Jab bhi koi feature banana ho, ye questions poochho:

1. Feature kya karega?
2. Kaunsa data chahiye?
3. Kya database mein koi change chahiye?
4. Input ko kaise validate karenge?
5. Kaunsa HTTP method aur endpoint chahiye?
6. Success, invalid input aur record na milne par kya response denge?
7. Swagger UI (`/docs`) mein ise kaise test karenge?

Har feature mein zaroori nahi ki saari files change hon. Sirf wahi files modify karo jinmein us feature ka kaam hota hai.

---

## 10. Khud se coding seekhne ka tarika

Har naye concept ke liye ye 3 stages follow karo:

**Stage 1 — Understand:** Code kya karta hai aur kyun karta hai, ye samjho.

**Stage 2 — Recall:** Bina notes dekhe explain karne ki koshish karo.

**Stage 3 — Build:** Chhota feature khud design karo, pehle logic socho, phir code likho aur test karo.

**Golden rule:** Code ki har line ratne ki zaroorat nahi hai. Uska purpose, flow aur file ki responsibility samajhna zyada important hai.




Notes mein likho: model_dump(exclude_unset=True) PATCH request mein sirf wahi fields deta hai jo user ne explicitly bheji hain. Isse baaki fields ki existing database values galti se overwrite hone se bach sakti hain.