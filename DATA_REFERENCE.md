# AZIL Insurance API — Data Reference

> **This is reverse-engineered, not authoritative.** Neither this repo nor
> `AZIL-FRONTEND` contains the backend source. Everything below was inferred from:
> - Client-side TypeScript interfaces in `AZIL-FRONTEND/src/**` (real typed shapes, but
>   hand-written by frontend devs — can drift from what the API actually returns).
> - `AZIL-FRONTEND/API Documentation.json`, an OpenAPI 3.1.1 file with 72 paths — but its
>   `components.schemas` is **empty**, so only endpoint paths/methods and a handful of
>   inline request-body schemas / response `examples` are usable, and several of those
>   examples are themselves placeholders (`{}`, `[]`).
> - Actual field access in this repo's `src/data/transforms.py` and `src/data/loaders.py`
>   (i.e. which keys downstream code actually reads off the JSON — the strongest signal,
>   since a typo there would break the app).
>
> Base URL: `https://azilinsurance.co.ke/backend/api`. Auth: `Authorization: Bearer <token>`.
> Most list responses are wrapped in an envelope `{ data: [...], total, page, limit }` or
> occasionally double-wrapped `{ data: { data: [...] } }` — see `src/services/api_client.py`
> `unwrap()` / `_extract_items()` for the exact unwrapping logic this repo relies on.
>
> Fields marked **`?`** or "unconfirmed" are inferred from a single TS interface, a single
> OpenAPI example, or a `[key: string]: any` catch-all — not from a formal schema. Treat
> them as a starting guess, not a guarantee. **Update this file if you discover the real
> API disagrees with it.**

---

## 1. Auth — Login

**Endpoint:** `POST /auth/login`

| Field | Type | Notes/Example |
|---|---|---|
| `email` | string | request body |
| `password` | string | request body, min length 6 |
| `token` | string | response; JWT, e.g. `"eyJhbGciOiJIUzI1NiIs..."` |
| `user` | object | response; typed as `any` on the frontend — see Auth/Me below for shape |
| `user.id` | string | example value `"…"` (placeholder in OpenAPI example) |
| `user.name` | string | example `"John Doe"` |
| `user.email` | string | example `"john@example.com"` |
| `user.roles` | array | example `[]` — element shape unconfirmed |

**Source:**
- `AZIL-FRONTEND/API Documentation.json` — `paths./api/auth/login.post` (request schema + response example)
- `AZIL-FRONTEND/src/services/client/login.ts:4-13` (`LoginCredentials`, `LoginResponse` — note `user: any`)
- `azil-metrics/src/services/api_client.py:53-66` (`login()` — reads `body.get("token") or body.get("data", {}).get("token")`, confirming the token can appear either top-level or nested under `data`)

---

## 2. Auth — Me (current user)

**Endpoint:** `GET /auth/me`

| Field | Type | Notes/Example |
|---|---|---|
| `data.id` | string | wrapped in `{data: {...}}` per OpenAPI example |
| `data.name` | string | example `"John Doe"` |
| `data.email` | string | example `"john@example.com"` |
| `data.roles` | array | example `[]`, element shape unconfirmed |
| `data.permissions` | array | example `[]`, element shape unconfirmed |
| `data.data` | object | **?** occasionally double-wrapped — azil-metrics unwraps twice defensively |

**Source:**
- `AZIL-FRONTEND/API Documentation.json` — `paths./api/auth/me.get` response example
- `azil-metrics/src/services/auth_api.py:18-24` — `unwrap(client.get("/auth/me"))`, then `if isinstance(me.get("data"), dict): me = me["data"]` with the comment *"some AZIL endpoints double-wrap: `{data: {data: {...user...}}}`"*
- `azil-metrics/src/services/auth_api.py:44` — `current_user_display_name()` reads `user.get("name") or user.get("email")`, confirming `name`/`email` are top-level keys on the unwrapped user object

---

## 3. Covers (Policies)

**Endpoints:**
- `GET /covers/` — list (paginated, filterable)
- `POST /covers/buy` — create a cover (bundles user + vehicle + cover + payment)
- `GET /covers/{cover}` — single cover (no OpenAPI example available)
- `GET /covers/vehicle/{registrationNumber}/search` — search covers by vehicle reg
- `PATCH /covers/{id}/restore` — restore a soft-deleted cover

| Field | Type | Notes/Example |
|---|---|---|
| `id` | string | |
| `product_price_id` | string | FK to `product_prices.id`; required on create |
| `start_date` | string (date) | `DD/MM/YYYY` on write; must be between yesterday and today+5 days. OpenAPI example: `"17/04/2026"` |
| `end_date` | string | read side; used by `transforms.py`/pages as a `_date`-suffixed column (auto-parsed to datetime) |
| `payment_type` | enum | `one_time` \| `installment` \| `daily` \| `credit` |
| `amount` | number | min 1; **the field the dashboard sums for "Premium volume"** |
| `premium` | number | min 1; distinct from `amount` (both exist as separate fields) |
| `channel` | enum | `web` \| `ussd` \| `whatsapp` \| `android` \| `ios` \| `agent` |
| `status` | string | e.g. `"active"`; pages filter on exact string `"active"` vs. everything else |
| `created_at` | string (datetime) | drives date-range filtering everywhere (`filter_by_date_range`) |
| `vehicle_id` | string | **?** inferred — `azil-metrics` merges vehicles onto covers via `vehicle_id` (see `link_customers_via_vehicles`) |
| `registration_number` | string | seen embedded when covers carry vehicle details (used as fallback source for "vehicle mix" chart if no `/vehicles/` data) |
| `make` / `model` | string | **?** embedded vehicle fields on some cover records — `7_Product_Rankings.py` falls back to `covers` columns containing `"make"` when the vehicles endpoint has none |
| `user` | object | embedded customer — see `find_customer_id_column`/`find_customer_name_column`; nested under one of `user`/`owner`/`client`/`customer` depending on endpoint, flattened by `pd.json_normalize` to e.g. `user_id`, `user_first_name`, `user_last_name`, `user_name`, `user_msisdn`, `user_phone_number` |
| `product` | object | embedded product; seen as `{ name: string }` minimum in one admin list page |
| `policy_number` | string | seen on a `Policy` shape alongside cover fields |
| `payment_mode` | string | seen on the same `Policy` shape |

**Buy request body** (`POST /covers/buy`) is a bundle of three sub-objects:
- `user`: `name`, `email`, `phone_number` (10–15 chars), `profile.{id_number, kra_pin, gender(male|female), type(admin|user|staff|agent), city, country, address, zip_code, metadata}`
- `vehicle`: `registration_number`, `chassis_number`, `engine_number`, `engine_capacity`, `model`, `make`, `year`(number), `color`, `type`(int enum 1-8), `value`(number), `files`(string[]), `passengers`(number), `body_type`, `windscreen_limit`, `entertainment_unit`
- `cover`: `product_price_id`, `start_date`, `payment_type`, `amount`, `premium`, `channel`
- Response: `{success, message, data: {payment: {}, cover: {}, vehicle: {}, user: {}}}` — OpenAPI example shows all four sub-objects as **empty placeholders**, so their actual returned shape is unconfirmed; assume same shape as the standalone Payment/Cover/Vehicle/User entities.

**Source:**
- `AZIL-FRONTEND/API Documentation.json` — `paths./api/covers/buy.post` (full request schema + response example)
- `AZIL-FRONTEND/src/services/client/policiesService.ts:1-93` (`CoverFilters`, `CoverPagination`, `listCovers`, `getCoverDetails`)
- `AZIL-FRONTEND/src/services/client/vehicle.ts:1-23` (`searchVehicleCovers`)
- `AZIL-FRONTEND/src/modules/admin/policies/pages/comprehensive/list.tsx:19-33` (`Product`, `Policy` interfaces with `user`, `product`, `policy_number`, `payment_mode`, `registration_number`, `status`, `start_date`, `end_date`)
- `azil-metrics/src/data/loaders.py:12-14` (`fetch_covers` → `GET /covers/`)
- `azil-metrics/src/data/transforms.py:137-178` (`find_customer_id_column`, `find_customer_name_column`, `link_customers_via_vehicles` — comments document the `User -> Vehicle -> Cover` chain and that `GET /vehicles/` takes `user_id`, `GET /covers/` takes `vehicle_id`)
- `azil-metrics/pages/1_Overview.py:44,48,73` (`covers["status"]`, `covers["id"]`, `covers["amount"].sum()`)
- `azil-metrics/pages/7_Product_Rankings.py:73` (fallback `make`/`model`-like column search on `covers`)

---

## 4. Payments

**Endpoints:**
- `GET /payments/` — list
- `GET /payments/{payment}` — single
- `PUT /payments/{payment}` — update
- `DELETE /payments/{payment}` — soft delete
- `PATCH /payments/{id}/restore` — restore

| Field | Type | Notes/Example |
|---|---|---|
| `_id` | string | present alongside `id` — both exist per TS interface |
| `id` | string | |
| `cover_id` | string | FK to cover; used by `azil-metrics` to link paid covers (`payments["cover_id"]`) |
| `amount` | number | |
| `reference` | string | |
| `mode` | enum | `cash` \| `mpesa` \| `card` |
| `status` | enum | `pending` \| `initialized` \| `success` \| `failed` \| `cancelled` \| `reversed` |
| `remarks` | string \| null | |
| `created_at` | string | |
| `updated_at` | string | |
| `deleted_at` | string \| null | |
| `cover` | `PaymentCover` \| null | embedded, see below |
| `stkResponses` | `StkResponse[]` | embedded array, see §5 |
| `income` | any \| null | **?** shape unconfirmed |

**Embedded `PaymentCover`** (distinct/richer shape than the top-level Cover in §3 — this is what the Payments admin API embeds):

| Field | Type | Notes |
|---|---|---|
| `_id`, `id` | string | |
| `product_price_id` | string | |
| `vehicle_id` | string | |
| `agent_id` | string \| null | |
| `policy_number_id` | string | |
| `start_date`, `end_date` | string | |
| `status` | string | |
| `amount`, `premium`, `remaining` | number | |
| `payment_type` | string | |
| `channel` | string | |
| `is_extendible` | boolean | |
| `certificate_number` | string \| null | |
| `certificate_id` | string \| null | |
| `cancellation_id` | number \| null | |
| `remarks` | string \| null | |
| `created_at`, `updated_at` | string | |
| `deleted_at`, `cancelled_at` | string \| null | |

**Filters accepted by `GET /payments/`:** `cover_id`, `status`, `mode`, `trashed` (`with`\|`only`\|`without`), `user_id`, `agent_id`, `vehicle_id`, `product_id`, `underwriter_id`, `page`, `limit`, `sort`, `order` (`asc`\|`desc`).

**Source:**
- `AZIL-FRONTEND/src/modules/admin/payments/api/api.ts:4-87` (`StkResponse`, `PaymentCover`, `Payment`, `PaymentFilters`, `UpdatePaymentData`)
- `azil-metrics/src/data/loaders.py:17-19` (`fetch_payments` → `GET /payments/`)
- `azil-metrics/pages/1_Overview.py:48` (`payments.loc[payments.get("status") == "success", "cover_id"]`)
- `azil-metrics/pages/6_Customer_Analysis.py:39` (`payments["status"] == "success"`)

---

## 5. STK (M-Pesa) Responses

**Endpoints:**
- `GET /stk-responses/` — list
- `GET /stk-responses/{stkResponse}` — single
- `POST /payment/stk-callback` — Safaricom's inbound callback (not called by clients; documented for completeness)

| Field | Type | Notes/Example |
|---|---|---|
| `_id` | string | |
| `id` | string | |
| `MerchantRequestID` | string | Safaricom merchant request ID |
| `CheckoutRequestID` | string | unique STK checkout ID, used to look up the payment |
| `ResponseCode` | string | |
| `ResponseDescription` | string | |
| `CustomerMessage` | string | |
| `MpesaReceiptNumber` | string | |
| `TransactionDate` | string | |
| `ResultCode` | string | `0` = success (per callback schema, though typed as `string` on the response record itself) |
| `ResultDesc` | string | |
| `payment_id` | string | FK to parent Payment |
| `created_at`, `updated_at` | string | |
| `deleted_at` | string \| null | |

**Inbound callback body** (`POST /payment/stk-callback`, for reference — this is what Safaricom posts, not something a client reads): `Body.stkCallback.{MerchantRequestID, CheckoutRequestID, ResultCode(int), ResultDesc, CallbackMetadata}` where `CallbackMetadata` is present only on success and contains `Amount`, `MpesaReceiptNumber`, `TransactionDate`, `PhoneNumber` (documented as free-form in OpenAPI, no sub-schema).

**Source:**
- `AZIL-FRONTEND/src/modules/admin/payments/api/api.ts:4-20` (`StkResponse`)
- `AZIL-FRONTEND/API Documentation.json` — `paths./api/payment/stk-callback.post.requestBody` (callback schema)
- `azil-metrics/src/data/loaders.py:22-24` (`fetch_stk_responses` → `GET /stk-responses/`)

---

## 6. Users

**Endpoints:**
- `GET /users/` (list, paginated) — also `GET /users?page=&page_size=` for `/users/agents` variant
- `GET /users/{id}` — single
- `POST /users/` — create; `PUT /users/{id}` — update
- `PATCH /users/{id}/status` (also called as `PATCH /users/updateuser` in one place) — toggle active status
- `GET /users/{id}/profile` — client-facing profile
- `POST /users/{id}/password/reset` — set password
- `GET /users/{id}/roles/` , `POST /users/{id}/roles`, `DELETE /users/{id}/roles/{roleId}` — role assignment
- `GET /users/{id}/sub-agents` — sub-agent listing
- `GET /users/productionranking`, `GET /users/commissionranking` — agent leaderboards (distinct from `/dashboard/agent-ranks`, see §11)
- `POST /users/new-agent` — create agent
- `POST /users/import` — bulk CSV import

| Field | Type | Notes/Example |
|---|---|---|
| `id` | string | OpenAPI list example shows `{data: [], total: 0, page: 1, limit: 15}` — empty, no field-level example |
| `name` | string | request body on create, max 255 |
| `email` | string | unique |
| `password` | string | write-only, min length 6 |
| `phone_number` | string | max 25; **note:** several TS interfaces alias this as `msisdn` client-side |
| `msisdn` | number \| string | seen as the display/search field in `userTable.tsx`; likely the same underlying value as `phone_number` under a different key depending on endpoint |
| `status` | enum | `active` \| `inactive` (create/list); some pages instead check `is_active` (boolean) or `active_status` (number 0/1) — **?** these three all appear to represent the same concept across different call sites, exact source-of-truth field is unconfirmed |
| `is_active` | boolean | seen on `User` in `userTable.tsx`, `createUser.tsx` |
| `active_status` | number | seen on `User`/`FormData` in `createUser.tsx` as a 0/1 companion to `is_active` |
| `roles` | string[] | array of role IDs/names on write; `azil-metrics` also just checks `users["status"]`/`users["active_status"]` presence, doesn't rely on exact values beyond `"active"`/`1` |
| `profile` | object | nested: `gender`(male\|female), `type`(admin\|user\|staff\|agent), `id_number`(≤100 chars), `kra_pin`(6–12 chars), `city`, `country`, `address`, `zip_code`, `date_of_birth`(datetime), `metadata`(string), plus `agent_id` seen in one `User.profile` shape |
| `total` | number | seen on the `userTable.tsx` `User` interface — meaning unconfirmed (likely a count of something, e.g. policies) |
| `id_number`, `total_recruits`, `total_production`, `total_invocation`, `total_commission`, `id_file`, `kra_file`, `cert_file` | various | **?** seen only on the `AgentDetails` page's `User` interface — agent-specific fields, not present on the base `users.ts` shapes |
| `created_at` | string | used by `azil-metrics` for the "Users" KPI trend (`users["created_at"]`) |

**Source:**
- `AZIL-FRONTEND/API Documentation.json` — `paths./api/users/.post.requestBody` (create schema), `paths./api/users/.get` (empty list example)
- `AZIL-FRONTEND/src/modules/admin/users/pages/userTable.tsx:12-19` (`User`: `id, name, msisdn, email, is_active, total`)
- `AZIL-FRONTEND/src/modules/admin/users/pages/listAgents.tsx:13-25` (`User`: adds `status`, `phone_number`, `profile.{type, agent_id}`)
- `AZIL-FRONTEND/src/modules/admin/users/pages/createUser.tsx:13-43` (`UserProfile`, `User`, `FormData` — `active_status`, `roles`)
- `AZIL-FRONTEND/src/modules/admin/users/pages/agentDetails.tsx:8-22` (agent-specific extras: `total_recruits`, `total_production`, `total_invocation`, `total_commission`, `id_file`, `kra_file`, `cert_file`)
- `AZIL-FRONTEND/src/modules/admin/users/api/users.ts:21-31,127-150` (`FetchUsers` from `/users/agents`, `CreateUserApi` from `/users`)
- `azil-metrics/src/data/loaders.py:27-29` (`fetch_users` → `GET /users/`)
- `azil-metrics/pages/13_User_Overview.py:28` (`users["status"] == "active"`)
- `azil-metrics/pages/1_Overview.py:65-69,84` (`users[active_col]` where `active_col` is `status` or `active_status`; `users["created_at"]`)

---

## 7. Products

**Endpoints:**
- `GET /products/` — list
- `POST /products/` — create
- `GET /products/{product}` , `PUT /products/{product}` — read/update
- `DELETE /products/{id}` — delete; `PATCH /products/{id}/restore` — restore
- `GET /products/{product}/installment`, `GET|POST /products/{product}/periods/`, `POST /products/{product}/periods/sync`
- `GET|POST /products/{product}/prices/`, `PUT /products/{product}/prices/{id}`
- `GET|POST /products/{product}/terms/`
- `GET|POST /products/{product}/valuers/`

| Field | Type | Notes/Example |
|---|---|---|
| `id` | string | |
| `name` | string | unique, 2–191 chars |
| `description` | string | |
| `product_type` | enum | `commercial` \| `private` \| `motor_cycle` \| `taxi` |
| `premium_type` | enum | `fixed` \| `slab` \| `percentage` (create schema); a separate `ProductState`/premium-creation payload elsewhere uses `fixed` \| `rate_based` — **?** these two enums may not be the same field |
| `has_tonnage` | boolean | |
| `has_installments` | boolean | |
| `product_installment_id` | string | required when `has_installments` is true |
| `has_sits` | boolean | |
| `type_of_certificate` | int enum | `1, 8, 4, 9, 10`; required when `product_type` is `motor_cycle`/`taxi` |
| `passengers` | integer | ≥1; required when `has_sits` true or `product_type` is `commercial`/`motor_cycle`/`taxi` |
| `tonnage` | number | ≥0.01; required when `has_tonnage` true or `product_type` is `commercial`/`motor_cycle` |
| `supported_periods` | string[] | ≥1 item |
| `vehicle_type` | int enum | `1`–`8`; required when `product_type` is `commercial`/`motor_cycle` |
| `type_of_cover` | int enum | `100, 200, 300` |
| `underwriter_id` | string | FK, must exist in `underwriters.id` |
| `has_valuation` | boolean | |
| `stamp_duty` | number | ≥0 |
| `phcf` | number | 0–100 |
| `training_levy` | number | ≥0 |
| `commission_rate` | number | 0–100 |
| `agent_rate` | number | **?** truncated in OpenAPI schema dump, likely 0–100 like `commission_rate` |
| `with_holding_tax` | number | seen only in `CmProductType` TS type, not in the OpenAPI create schema — **?** unconfirmed on this endpoint |
| `is_active` | boolean | seen as `ProductValues.is_active` in admin form type |
| `subtype` | string | seen on `Product` interface in `underwriterDetails.tsx` and `ProductValues` |
| `number_of_certificates` | number | seen on `Product` in `underwriterDetails.tsx` |
| `underwriter_name` | string | **not** a real API field — `azil-metrics` derives it client-side by mapping `products["underwriter_id"]` through the underwriters lookup (`7_Product_Rankings.py:26-27`) |
| `periods` | `Period[]` | embedded on read, `{id, description}[]` per `quote.tsx` |

**Source:**
- `AZIL-FRONTEND/API Documentation.json` — `paths./api/products/.post.requestBody` (full create schema)
- `AZIL-FRONTEND/src/modules/admin/underwriters/types/types.ts:1-56` (`ProductValues`, `CmProductType`)
- `AZIL-FRONTEND/src/modules/admin/underwriters/pages/underwriterDetails.tsx:12-18` (`Product`: `id, name, is_active, number_of_certificates, subtype`)
- `AZIL-FRONTEND/src/modules/client/motor/products/pages/Product.tsx:19-31` (`Period`, `Product` with `periods`, `tonnage`, `has_sits`, `passengers`, `has_tonnage`, `vehicle_type`)
- `AZIL-FRONTEND/src/modules/admin/underwriters/api/api.ts:648-665` (`createProductPremium` payload: `period_id`, `seating_capacity`, `tonnage`, `underwriter_premium`, `agent_premium`, `direct_premium`, `ussd_premium`, `recruit_cut`, `minimum_amount`, `minimum_premium`, `premium_type: 'fixed'|'rate_based'`, `status` — this is the **product price/premium** sub-resource, not the product itself)
- `azil-metrics/src/data/loaders.py:32-34` (`fetch_products` → `GET /products/`)
- `azil-metrics/pages/7_Product_Rankings.py:25-27,53` (`products["underwriter_id"]`, `products["product_type"]`, derived `underwriter_name`)

---

## 8. Vehicles

**Endpoints:**
- `GET /vehicles/` — list (accepts `user_id` filter, per `azil-metrics` comment)
- `GET /vehicles/{vehicle}`, `PUT /vehicles/{vehicle}`
- `DELETE`/`PATCH /vehicles/{id}/restore`
- `GET /vehicles/{vehicle}/covers` — covers for a vehicle
- `GET /covers/vehicle/{registrationNumber}/search` — search (see §3)

| Field | Type | Notes/Example |
|---|---|---|
| `registration_number` | string | |
| `chassis_number` | string | |
| `engine_number` | string | in the `/covers/buy` sub-schema; not present in the client-side `VehicleData` form type (§ below) — **?** possibly added server-side or optional |
| `engine_capacity` | string | |
| `model` | string | |
| `make` | string | |
| `year` | number | in `/covers/buy` schema |
| `start_date` | string | **?** seen only in the client-side `VehicleData` form (may be cover-related, not a true vehicle field — possibly a form artifact) |
| `color` / `vehicle_color` | string | `/covers/buy` schema calls it `color`; client form type calls it `vehicle_color` — **?** likely the same underlying field, naming differs by call site |
| `type` | int enum | `1`–`8`, vehicle body/category type |
| `body_type` | string | |
| `other_body_type` | string | **?** form-only field, likely used when `body_type` is "other" |
| `other_make` | string | **?** form-only, likely used when `make` is "other" |
| `value` | number | ≥0, insured value |
| `files` | string[] | attachment IDs (e.g. logbook) |
| `passengers` | number | ≥0 |
| `windscreen_limit` | string | |
| `entertainment_unit` | string | |
| `sacco` | string | **?** form-only field, SACCO/PSV association — unconfirmed as a real persisted vehicle field vs. form-only |
| `is_ntsa_verified` | boolean | **?** form-only, optional |
| `owner_id` / `user_id` | string | **?** inferred — `azil-metrics` looks for one of `user_id, owner_id, customer_id, client_id, user_user_id, vehicle_owner_id` as the FK from vehicle to owning user (see `CUSTOMER_ID_CANDIDATES` in transforms.py); exact key not confirmed by any TS interface |

**Source:**
- `AZIL-FRONTEND/API Documentation.json` — `paths./api/covers/buy.post.requestBody.properties.vehicle` (write schema used during cover purchase)
- `AZIL-FRONTEND/src/modules/agent/store/vehicleStore.ts:4-19` (`VehicleData` — client-side form state, not confirmed to match API read shape 1:1)
- `AZIL-FRONTEND/src/services/client/vehicle.ts` (`searchVehicleCovers`, no explicit response type — untyped)
- `azil-metrics/src/data/loaders.py:37-42` (`fetch_vehicles` → `GET /vehicles/`, wrapped in try/except since it may 404 on some tenants)
- `azil-metrics/src/data/transforms.py:137-178` (`CUSTOMER_ID_CANDIDATES`, `link_customers_via_vehicles` — comment: *"`GET /vehicles/` takes `user_id` (Filter by owner)"*)
- `azil-metrics/pages/7_Product_Rankings.py:69-74` (searches `vehicles.columns` for anything containing `"make"`)

---

## 9. Underwriters

**Endpoints:**
- `GET /underwriters/` — list
- `POST /underwriters/` — create
- `GET /underwriters/{underwriter}`, `PUT /underwriters/{underwriter}` — read/update
- `PATCH /underwriters/{id}/restore` — restore
- `GET /underwriters/{underwriter}/declarations` — declarations report (filters: `from`, `to`, `export`)

| Field | Type | Notes/Example |
|---|---|---|
| `id` | string | |
| `name` | string | unique, 3–191 chars |
| `dmvic_member_id` | integer | unique, ≥1 |
| `email` | string | unique |
| `phone_number` | string | unique, ≤25 chars |
| `image` | string | ≤500 chars, required on create |
| `description` | string | required on create |
| `status` | enum | `active` \| `inactive` |
| `slug` | string | unique, ≤191 chars |

Required on create: `name`, `dmvic_member_id`, `email`, `phone_number`, `image`, `description`.

**Source:**
- `AZIL-FRONTEND/API Documentation.json` — `paths./api/underwriters/.post.requestBody` (full create schema incl. required list)
- `AZIL-FRONTEND/src/modules/admin/underwriters/pages/listUnderwriters.tsx:13-23` (`Underwriter`: matches OpenAPI fields exactly)
- `AZIL-FRONTEND/src/modules/admin/underwriters/api/api.ts:10-18` (`FetchUnderwriters` → `GET /underwriters`)
- `azil-metrics/src/data/loaders.py:45-48` (`fetch_underwriters` → `GET /underwriters/`)

---

## 10. Dashboard Trends

All trend endpoints share the response envelope `{ data: { trends: [...], totals?: {...} } }`
(the `data.trends[]` array is what `azil-metrics`' `extract_trend_df()` reads). Common
query filters across most of these: `from`, `to`, `channel` (`web`\|`ussd`\|`whatsapp`\|`ios`\|`android`\|`agent`), `user_id`, `agent_id`, `product_id`, `period_id`, `status`, `underwriter_id` — not every endpoint accepts every filter; see each TS wrapper for the exact accepted set.

### 10.1 Cover Trends

**Endpoint:** `GET /dashboard/cover-trends` (note: `to` is required per the `admin/api/api.ts` typing, though `services/client/dashboardService.ts`'s version treats it as optional)

| Field | Type | Notes |
|---|---|---|
| `trends` | array | list of `{date, count?, amount?, ...}` — `extract_trend_df` auto-detects the date key from `date`\|`period`\|`day` and the value key from `count`\|`amount`\|`income`\|`total` |
| `status` (filter) | string | e.g. `active` |

**Source:** `AZIL-FRONTEND/src/services/client/dashboardService.ts:1-42`, `AZIL-FRONTEND/src/modules/admin/api/api.ts:144-198`, `azil-metrics/src/data/loaders.py:51-53`, `azil-metrics/src/data/transforms.py:63-76`

### 10.2 Income Trends

**Endpoint:** `GET /dashboard/income-trends`

| Field | Type | Notes |
|---|---|---|
| `trends` | array | consumed via `extract_trend_df(..., value_candidates=("income","total","amount"))` |
| `totals.income` | number | used directly for the "Azil Income" KPI card |

**Source:** `AZIL-FRONTEND/src/modules/admin/api/api.ts:89-140`, `azil-metrics/src/data/loaders.py:56-58`, `azil-metrics/pages/1_Overview.py:71,113-116`

### 10.3 Expiration Trends

**Endpoint:** `GET /dashboard/expiration-trends`

**Status: unconfirmed / no TS usage found.** This repo (`azil-metrics`) calls it and expects
the same `{data: {trends: [...]}}` envelope as the other trend endpoints, but no matching
call site was found anywhere in `AZIL-FRONTEND`'s own code or in the OpenAPI file's path
list. It may exist on the real backend without a frontend consumer yet, or the path/shape
here could be wrong — verify against the live API before relying on it.

**Source:** `azil-metrics/src/data/loaders.py:71-73` (`fetch_expiration_trends`) — sole source; no corroboration found.

### 10.4 Renewal Trends

**Endpoint:** `GET /dashboard/renewal-trends`

| Field | Type | Notes |
|---|---|---|
| `granularity` (filter) | enum | `day` \| `week` \| `month` \| `year` |
| `data.trends` / `data.rows` | array | code checks for either key name, plus a bare array, plus `data.totals` as alternate success signals — **?** exact key not settled even in the frontend's own code |

**Source:** `AZIL-FRONTEND/src/modules/agent/api/agent.ts:2181-2260` (`fetchRenewalTrends`), `azil-metrics/src/data/loaders.py:76-78`

### 10.5 Underwriter Trends

**Endpoint:** `GET /dashboard/underwriter-trends`

Unlike the flat `trends[]` arrays above, this endpoint nests a per-underwriter breakdown
inside each period:

| Field | Type | Notes |
|---|---|---|
| `trends[].date` | string | period date |
| `trends[].underwriters` | array | per-underwriter breakdown for that period |
| `trends[].underwriters[].underwriterId` | string/number | |
| `trends[].underwriters[].underwriterName` | string | |
| `trends[].underwriters[].totalAmount` | number | |
| `trends[].underwriters[].coverCount` | number | |
| `trends[].underwriters[].underwriterIncome` | number | |
| `underwriter_id` (filter) | number | |

**Source:** `AZIL-FRONTEND/src/modules/admin/reports/api/reports.ts:414-470` (`FetchUnderwriterTrends`), `azil-metrics/src/data/transforms.py:107-134` (`flatten_underwriter_trends` — the exact nested shape is documented in its docstring and confirmed by the admin reports page's own `trends.flatMap(...)` pattern), `azil-metrics/pages/12_Underwriter_Reports.py:24,34-38`

### 10.6 Underwriter Ranks (bonus — related but distinct endpoint)

**Endpoint:** `GET /dashboard/underwriter-ranks`

**Status: unconfirmed.** `azil-metrics` calls this defensively (catches `ApiError` and falls
back to deriving rankings from `underwriter-trends` instead) specifically because — per its
own code comment — *"this endpoint has no confirmed usage anywhere in AZIL-FRONTEND's own
code, so it may not be wired to real data on this backend."* Treat as speculative.

**Source:** `azil-metrics/src/data/loaders.py:81-89`

---

## 11. Agent Ranks

**Endpoint:** `GET /dashboard/agent-ranks`

| Field | Type | Notes/Example |
|---|---|---|
| `name` | string | agent display name, read as `item.name` |
| `count` | number | policies sold, read as `item.count` |
| `premium` | number | total premium, read as `item.premium` |
| `user_id` | string/number | **?** one of three candidate ID fields |
| `agent_id` | string/number | **?** one of three candidate ID fields |
| `id` | string/number | **?** fallback if neither `user_id` nor `agent_id` present |

Not a typed TS interface anywhere — every call site types the array as `any[]` and reads
fields defensively/optionally. Filters: `from`, `to`, `status`.

Note: distinct from `GET /users/productionranking` and `GET /users/commissionranking`,
which are separate leaderboard endpoints under Users (§6) — this repo (`azil-metrics`)
only consumes `/dashboard/agent-ranks`.

**Source:**
- `AZIL-FRONTEND/src/modules/admin/api/api.ts:202-245` (`FetchAgentRanks`, untyped `filters`/return)
- `AZIL-FRONTEND/src/modules/admin/dashboard/dashboard.tsx:305-309` (`item.name`, `item.count`, `item.premium`)
- `AZIL-FRONTEND/src/modules/admin/reports/pages/reports.tsx:719-743` (`item.user_id || item.agent_id || item.id`, `item.name`, `item.count`, `item.premium`)
- `azil-metrics/src/data/loaders.py:61-63` (`fetch_agent_ranks` → `GET /dashboard/agent-ranks`)
- `azil-metrics/pages/1_Overview.py:148-150` (`agent_ranks["premium"]`, `name_col` fallback between `"name"`/`"agent_name"`)

---

## 12. Product Sales

**Endpoint:** `GET /dashboard/product-sales`

| Field | Type | Notes/Example |
|---|---|---|
| `name` | string | product name |
| `amount` | number | total sales amount — used for ranking/sorting |
| `premium` | number | |
| `count` | number \| undefined | optional, per TS interface |

Filters: `from`, `to`, `status` (admin API); the agent-side `fetchProductSales` additionally
accepts `user_id`, `agent_id`, `product_id`, `period_id`, `underwriter_id`.

**Source:**
- `AZIL-FRONTEND/src/modules/admin/charts/ProductSalesBarChart.tsx:23-28` (`ProductSalesData: {name, amount, premium, count?}`)
- `AZIL-FRONTEND/src/modules/admin/api/api.ts:41-84` (`FetchProductSales`)
- `AZIL-FRONTEND/src/modules/agent/api/agent.ts:2262-2289+` (`fetchProductSales`, extended filter set)
- `azil-metrics/src/data/loaders.py:66-68` (`fetch_product_sales` → `GET /dashboard/product-sales`)
- `azil-metrics/pages/7_Product_Rankings.py:40-43` (`product_sales["amount"]`, `product_sales["name"]`)

---

## 13. WhatsApp Sessions

**Endpoints:**
- `GET /whatsapp/sessions/` — list (filters: `status`, `step`, `phone_number`, `from`, `to`, `page`, `limit`, `export`)
- `GET /whatsapp/sessions/{id}` — single
- `GET /whatsapp/sessions/contacts` — distinct customers aggregated by phone number
- `GET /whatsapp/sessions/insights` — summary analytics

| Field | Type | Notes/Example |
|---|---|---|
| `id` | string | |
| `phone_number` | string | |
| `status` | enum | `active` \| `completed` \| `abandoned` |
| `step` | string | current funnel step |
| `created_at`, `updated_at` | string | |
| *(catch-all)* | any | interface has `[key: string]: any` — more fields likely exist unlisted |

**List response wrapper:** `{data: WhatsappSession[], total?, page?, limit?, pagination?: {total, page, limit, lastPage?}, meta?: {total, page, limit}}` — **?** pagination metadata key is inconsistent (`pagination` vs `meta` vs top-level `total`/`page`/`limit`), all marked optional, so don't assume all three exist together.

**Contacts response** (`GET /whatsapp/sessions/contacts`):

| Field | Type | Notes |
|---|---|---|
| `Name` | string? | note: PascalCase key, unusual vs. rest of API |
| `Email` | string? | |
| `Phone` | string | required |
| `Sessions` | number | |
| `Completed` | number | |
| `Abandoned` | number | |
| `Last Accessed` | string | literal key with a space |

Contacts response wrapper also includes `pagination: {total, page, limit, lastPage}` (all required, unlike sessions) and `period: {from, to}`.

**Insights response** (`GET /whatsapp/sessions/insights`, filters `from`/`to` only):

| Field | Type | Notes |
|---|---|---|
| `total_sessions` | number | |
| `unique_users` | number | |
| `completion_rate` | number | |
| `step_funnel` | array | `{step, count, drop_off_rate?}[]` |

**Source:**
- `AZIL-FRONTEND/src/modules/admin/policies/api/policyApi.ts:777-994` (`WhatsappSessionFilters`, `WhatsappSession`, `WhatsappSessionsResponse`, `WhatsappContactFilters`, `WhatsappContact`, `WhatsappContactsResponse`, `WhatsappSessionInsightsFilters`, `WhatsappSessionInsights`)
- `azil-metrics/src/data/loaders.py:97-110` (`fetch_whatsapp_sessions` → `GET /whatsapp/sessions/`, `fetch_whatsapp_insights` → `GET /whatsapp/sessions/insights`, both wrapped in try/except)

---

## 14. USSD Sessions

Structurally identical to WhatsApp Sessions (§13) — same field names, same interface shapes, separate endpoint namespace.

**Endpoints:**
- `GET /ussd/sessions/` — list (same filters as WhatsApp: `status`, `step`, `phone_number`, `from`, `to`, `page`, `limit`, `export`)
- `GET /ussd/sessions/{id}` — single
- `GET /ussd/sessions/contacts` — distinct customers
- `GET /ussd/sessions/insights` — summary analytics

| Field | Type | Notes |
|---|---|---|
| `id` | string | |
| `phone_number` | string | |
| `status` | enum | `active` \| `completed` \| `abandoned` |
| `step` | string | |
| `created_at`, `updated_at` | string | |
| *(catch-all)* | any | `[key: string]: any` |

Response envelopes, contacts shape (`Name`, `Email`, `Phone`, `Sessions`, `Completed`,
`Abandoned`, `Last Accessed`), and insights shape (`total_sessions`, `unique_users`,
`completion_rate`, `step_funnel[]`) are identical in structure to §13 — see that section
for the field tables.

**Source:**
- `AZIL-FRONTEND/src/modules/admin/ussd/api/api.ts:1-257` (`UssdSessionFilters`, `UssdSession`, `UssdSessionsResponse`, `UssdContactFilters`, `UssdContact`, `UssdContactsResponse`, `UssdSessionInsightsFilters`, `UssdSessionInsights`)
- `azil-metrics/src/data/loaders.py:113-126` (`fetch_ussd_sessions` → `GET /ussd/sessions/`, `fetch_ussd_insights` → `GET /ussd/sessions/insights`)

---

## 15. Audit Logs

**Endpoints:**
- `GET /audit-logs/` — list
- `GET /audit-logs/{id}` — single
- `DELETE /audit-logs/{id}` — delete

**Filters:** `user_id`, `action`, `model`, `model_id`, `start_date`, `end_date`, `deleted`, `page`, `limit`.

No TS interface exists for the record shape itself — everything is typed as the generic
`call()` response with untyped `data`. Field names below are inferred only from the filter
parameter names (a weak signal — filters don't guarantee matching response field names)
and general REST/audit-log convention; **treat every field here as unconfirmed**.

| Field | Type | Notes |
|---|---|---|
| `id` | string | inferred from `/audit-logs/{id}` path param and `DELETE`/`GET` single-record calls |
| `user_id` | string | **unconfirmed** — inferred from filter name only |
| `action` | string | **unconfirmed** — inferred from filter name only |
| `model` | string | **unconfirmed** — inferred from filter name only (likely the model/table name the log entry is about) |
| `model_id` | string | **unconfirmed** — inferred from filter name only |
| `created_at` / `start_date` / `end_date` range | string | **unconfirmed** — filters are named `start_date`/`end_date` rather than `from`/`to` used elsewhere, so the underlying date column name is unclear |
| `deleted` | string | **unconfirmed** filter — presumably a soft-delete flag |

**Source:**
- `AZIL-FRONTEND/src/modules/admin/api/api.ts:248-375` (`FetchAuditLogs`, `FetchAuditLog`, `DeleteAuditLog` — filters only, no record-shape typing anywhere)
- `azil-metrics/src/data/loaders.py:129-134` (`fetch_audit_logs` → `GET /audit-logs/`, wrapped in try/except)

---

## Endpoints referenced by `azil-metrics` with no corroborating AZIL-FRONTEND usage

For visibility: besides §10.3 (expiration-trends) and §10.6 (underwriter-ranks) called out
above, every other endpoint this repo calls (`src/data/loaders.py`) has at least one
matching call site in `AZIL-FRONTEND`. If a live API call to expiration-trends or
underwriter-ranks ever returns unexpected data, that's the first place to look — those two
are the least-verified endpoints in this whole document.
