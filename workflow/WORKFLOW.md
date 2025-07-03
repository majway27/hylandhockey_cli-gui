# Workflow

> Workflow is the business logic

1. Register Intake
2. Register Validation
3. Register Approval
3. Order Intake
4. Order Validation
5. Order Verification
6. Order Acceptance
7. Order Approval
8. Order Submission

## Register

### Register Flow

Roles: ['Participant', 'Order Manager']

1. Register Intake
    - A **registration** is created that contains `participant` details, including jersey information.
2. Register Validation
    - The **registration** is reviewed.
3. Register Approval
    - The **registration** is approved.

## Order

### Order Flow

Roles: ['Participant', 'Order Manager']

1. Order Intake
    - The **order** is based on a select set of details provided by the `participant` in their approved **registration**.
    - The `order manager` composes the **order** based on these details.
2. Order Validation
    - The `order manager` reviews the details and identifies any possible errors made by the `participant`.
3. Order Verification
    - The `participant` is sent a confirmation email by the `order manager`.
    - The email shows the details that will be used for the **order**.
    - If there are any possible errors, they are listed in the email for resolution by the `participant`.
4. Order Acceptance
    - The `particpant` replies to the email and either confirms the **order** as-is, or modifies it.
    - This ensures the `participant` agrees and is responsible for the **order** contents.
5. Order Approval
    - The `order manager` processes the email response, and approves the finalized **order** contents.
6. Order Submission
    - The `order manager` orders a jersey set, using the confirmed details.

### Order Notification

- The email notification message body will be html format, never plain text.

#### Order Verification Email Template

```md
FROM: 
TO: 
SUBJECT: Good morning, here is what you ordered for _ during registration:

- Jersey Name: 
- Jersey #: 
- Jersey Size: 
- Jersey Type: 
- Sock Size: 
- Sock Type: 
- Pant Shell Size: 

Link

We do have samples available if you need to check the sizing but otherwise if everything looks good let me know and we'll get the order placed.

<signiture block>
```