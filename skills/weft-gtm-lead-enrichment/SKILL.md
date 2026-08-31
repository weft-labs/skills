---
name: weft-gtm-lead-enrichment
description: Use whenever an agent runs GTM lead enrichment through Weft with OneShot Agent, mentions win.oneshotagent.com, enriches a LinkedIn profile, finds or verifies a work email, retrieves a social newsfeed, or needs to recover the result of a paid OneShot async request. Covers the paid POST, request_id extraction, free GET result polling with X-Agent-ID, and the current Weft MCP free-200 limitation. Load weft too when payment uses Weft.
---

# OneShot Agent Async Tools

OneShot is the best provider from Weft's 2026-08-17 one-profile trial. Treat
that as a useful first result, not a population benchmark.

## Endpoints

| Need | Paid POST | Body | Observed price |
|---|---|---|---:|
| LinkedIn profile | `https://win.oneshotagent.com/v1/tools/enrich/profile` | `{"linkedin_url":"https://www.linkedin.com/in/<slug>/"}` | $0.005 |
| Work-email candidate | `https://win.oneshotagent.com/v1/tools/enrich/email` | `{"full_name":"<name>","company_domain":"example.com"}` | $0.005 |
| Email deliverability | `https://win.oneshotagent.com/v1/tools/verify/email` | `{"email":"person@example.com"}` | $0.001 |
| Recent social newsfeed | `https://win.oneshotagent.com/v1/tools/research/newsfeed` | `{"social_media_url":"https://www.linkedin.com/in/<slug>/"}` | $0.010 |

The merchant's live `402` quote is authoritative. The prices above are only
the prices observed in the trial.

## Required Flow

### 1. Choose one agent ID

Set `X-Agent-ID` to the buyer wallet address or a stable agent UUID. Send the
same value on the paid POST and every result GET. Keep the request ID and agent
ID together until the job finishes.

### 2. Pay once

With Weft, call `weft_fetch` once:

```json
{
  "url": "https://win.oneshotagent.com/v1/tools/enrich/profile",
  "method": "POST",
  "body": "{\"linkedin_url\":\"https://www.linkedin.com/in/<slug>/\"}",
  "headers": {
    "content-type": "application/json",
    "X-Agent-ID": "<buyer-wallet-or-agent-uuid>"
  },
  "max_cost_usd": "0.005"
}
```

Decode `body_base64` if Weft returns it. The accepted JSON contains at least:

```json
{
  "request_id": "<id>",
  "tool": "<tool>",
  "status": "queued"
}
```

Preserve the Weft receipt and `request_id`. Do not repeat the paid POST after
a timeout or ambiguous response because a retry can create a second charge.

### 3. Read the result for free

Poll OneShot directly. This GET is free and must use the same `X-Agent-ID`:

```bash
curl --fail-with-body --silent --show-error \
  --header "X-Agent-ID: $AGENT_ID" \
  "https://win.oneshotagent.com/v1/requests/$REQUEST_ID"
```

Handle the response by `status`:

- `pending` or `processing`: retry only this free GET after a short wait.
- `completed`: return the `result` field to the user.
- `failed`: return the `error`; do not repeat the paid POST automatically.
- HTTP `404`: check both `request_id` and `X-Agent-ID`.

Use bounded polling. Stop and report the pending request ID when the time limit
is reached; the user can resume the free GET later.

## Completed Response Shapes

OneShot's OpenAPI types the job envelope but leaves `result` untyped. The
examples below are the shapes observed in the 2026-08-17 trial. Parse fields
defensively because provider result fields can change.

Every completed GET uses this outer envelope:

```json
{
  "request_id": "<request-id>",
  "status": "completed",
  "tool": "research",
  "result": {},
  "error": null,
  "error_code": null,
  "created_at": "<ISO-8601 timestamp>",
  "updated_at": "<ISO-8601 timestamp>"
}
```

Do not route by the outer `tool` value. All four observed responses used the
generic value `research`; route by the endpoint that created the request.

### Profile enrichment result

`POST /v1/tools/enrich/profile` placed this object in the outer `result`:

```json
{
  "status": "completed",
  "profile": {
    "email": null,
    "phone": null,
    "title": "<current title>",
    "emails": [],
    "phones": [],
    "skills": [],
    "company": "<current company>",
    "summary": "<profile summary>",
    "location": "<location>",
    "altemails": [],
    "education": [
      {
        "degree": "<degree>",
        "period": "<start - end>",
        "school": "<school>"
      }
    ],
    "full_name": "<full name>",
    "fullphone": [],
    "last_name": "<last name>",
    "experience": [
      {
        "title": "<role title>",
        "period": "<start - end or Present>",
        "company": "<company>",
        "company_website": "<URL>"
      }
    ],
    "first_name": "<first name>",
    "linkedin_url": "<LinkedIn URL>",
    "company_domain": "<domain>",
    "best_work_email": null,
    "apollo_person_id": null,
    "best_personal_email": null
  },
  "request_id": "<request-id>",
  "completed_at": "<ISO-8601 timestamp>",
  "receipt_id": "<receipt-id>",
  "cost": 0.005
}
```

Empty arrays and `null` are normal. Do not convert them into claims that the
person has no skills, phone, or email; they mean this response did not return
those values.

### Email lookup result

`POST /v1/tools/enrich/email` placed this object in the outer `result`:

```json
{
  "email": "person@example.com",
  "found": true,
  "status": "completed",
  "full_name": "<full name>",
  "request_id": "<request-id>",
  "completed_at": "<ISO-8601 timestamp>",
  "company_domain": "example.com",
  "receipt_id": "<receipt-id>",
  "cost": 0.005
}
```

Treat `found: true` as a candidate only. It does not mean the mailbox is
valid or deliverable.

### Email verification result

`POST /v1/tools/verify/email` placed this object in the outer `result`:

```json
{
  "email": "person@example.com",
  "valid": false,
  "status": "completed",
  "catch_all": false,
  "disposable": false,
  "request_id": "<request-id>",
  "deliverable": false,
  "completed_at": "<ISO-8601 timestamp>",
  "receipt_id": "<receipt-id>",
  "cost": 0.001
}
```

Use `deliverable` as the send gate. Preserve `valid`, `catch_all`, and
`disposable` as supporting evidence.

### Newsfeed result

`POST /v1/tools/research/newsfeed` has one extra nesting level: the outer
`result` contains another `result` object.

```json
{
  "result": {
    "url": "<requested profile URL>",
    "source": "linkedin",
    "newsfeed": [
      {
        "id": "urn:li:activity:<id>",
        "url": "<public post URL>",
        "type": "image",
        "media": [
          {
            "image_url": "<temporary media URL>",
            "video_url": "<optional temporary video URL>"
          }
        ],
        "author": {
          "headline": "<author headline>",
          "username": "<LinkedIn handle>",
          "image_url": "<temporary profile image URL>",
          "profile_url": "<LinkedIn profile URL>",
          "display_name": "<display name>"
        },
        "source": "linkedin",
        "article": {
          "url": "<optional article URL>",
          "type": "<optional article type>",
          "title": "<optional article title>",
          "thumbnail": "<optional temporary image URL>",
          "description": "<optional description>"
        },
        "content": "<post text>",
        "engagement": {
          "likes": 2,
          "shares": 0,
          "reposts": 0,
          "comments": 0,
          "total_reactions": 2
        },
        "owner_role": "author",
        "date_posted": "<ISO-8601 timestamp>",
        "platform_id": "<LinkedIn activity ID>"
      }
    ],
    "username": "<LinkedIn handle>"
  },
  "status": "completed",
  "request_id": "<request-id>",
  "completed_at": "<ISO-8601 timestamp>",
  "receipt_id": "<receipt-id>",
  "cost": 0.01
}
```

Newsfeed items vary by `type`:

- `media` and `article` are optional.
- Reaction-specific keys such as `love`, `funny`, `insight`, `support`, and
  `celebrate` can appear inside `engagement`.
- A repost uses `owner_role: "owner_feed_repost"` and puts the original post
  under `related_post`; the top-level repost item can have no `content` or
  `url`.
- Engagement values in `related_post` were strings in the observed payload,
  while normal item engagement values were numbers. Normalize before totals.
- LinkedIn media URLs are temporary. Preserve the public post URL and content;
  do not treat media URLs as durable assets.

## Current Weft Limitation

Do not call the free result URL with `weft_fetch` today. OneShot correctly
returns HTTP `200` without a `402` challenge, but Weft currently reports that
as `MERCHANT_RETURNED_NON_402`. Use direct HTTP or `curl` for
`GET /v1/requests/{id}`. This workaround does not make a second payment.

## Data Rules

- A found email is only a candidate. Call `/v1/tools/verify/email` and reject
  it when `deliverable` is false.
- Report profile/newsfeed conflicts instead of silently choosing one field.
- State the actual paid amount and that the result came from OneShot.
- Never print payment proofs, wallet keys, or buyer credentials.
