# tasq-api
The Tasq REST API enables you to interact with Tasq programmatically. Use this API to build apps, script interactions with Tasq, or develop any other type of integration. This page documents the REST resources available in Tasq, including the HTTP response codes and example requests and responses.


## Version and URI
This documentation is for version 1 of the Tasq platform REST API, which is the latest version.

The URIs for resources have the following structure:

https://api.tasqinc.com/v1/<resource-name>


## Authentication and authorization
You can create a personal access token and use it in place of a password when performing operations over HTTPS with Tasq using the API

### Creating a token
1. Login to {OPERATOR}.tasqinc.com.
2. In the upper-right corner of the Ops tab, select the gear icon.
3. Scroll to the "Personal access tokens" section.
4. Click to "Generate token".
5. Give your token a descriptive name.
6. Click to copy the token to your clipboard. For security reasons, after you navigate off the page, you will not be able to see the token again.

### Headers
Please provide your personal access token in the header for each REST request:
```authorization: <TOKEN>```

## Profile
This is an object representing a Tasq user profile.  You can retrieve it to see properties on the account like the current e-mail address, user role, team, etc.

*GET /v1/profile/{user_email}*

Returns user profile.

**Request**
*PATH PARAMETERS*
user_email `REQUIRED`

Example request
```
api.tasqinc.com/v1/profile/{user_email}
```
Example response
```
{
    "username": "tasq@tasqinc.com",
    "user_id": "8e69e0b9-4e2f-4b8b-97e4-2c107be4d99d",
    "accepting_tasqs": true,
    "teams": [
        "Team_1"
    ],
    "user_phone_number": "+13035555555"
}
```

`200`: Returned if the request is successful.
`401`: Returned if the authentication credentials are incorrect or missing.
`403`: Returned if the user is not an administrator.
`404`: Returned if the role is not found.




*PUT /v1/profile*

Updates user profile.

**Request**
*BODY PARAMETERS*
username: String `REQUIRED`
Roles: Array
PhoneNumber: String
AcceptingTasqs: Boolean
Team: Array


Example request
```
{
  "username":"john@tasqinc.com",
  "PhoneNumber":"+13035555555",
  "AcceptingTasqs":true,
  "Team":["Team_1"]
}
```
Example response
```
{
  "Username": {username},
  "Error": False,
  "Success": True
}
```

`200`: Returned if the request is successful.
`401`: Returned if the authentication credentials are incorrect or missing.
`403`: Returned if the user is not an administrator.
`404`: Returned if the role is not found.




## Tickets
This is an object representing a Tasq user ticket.  You can post tickets directly to Tasq support.


*POST /v1/tickets*

Create a new support ticket.

**Request**
*BODY PARAMETERS*
Username: String `REQUIRED`
Description: String `REQUIRED`
TicketTitle: String `REQUIRED`
IssueType: String (BUG | FEEDBACK | REQUEST) `REQUIRED`
Page: String (OPS | MY_TASQS | WORKFLOW) `REQUIRED`
Operator: String `REQUIRED`


Example request
```
{
  "Username":"{username}",
  "Description":"{description}",
  "TicketTitle":"{ticket_title}",
  "IssueType":"{issue_type}",
  "Page":"{page}",
  "Operator":"{operator}"
}
```
Example response
```
{
  "Error":False,
  "Success":True,
  "TicketName":Ticket Name,
  "TicketId":40,
}
```

`200`: Returned if the request is successful.
`401`: Returned if the authentication credentials are incorrect or missing.
`403`: Returned if the user is not an administrator.
`404`: Returned if the role is not found.



## Tasqs
This is an object representing Tasq lists.  You can retrieve it to see a list of tasqs.

*GET /v1/profile/{user_email}*

Returns user profile.

**Request**
*PATH PARAMETERS*
user_email `REQUIRED`

Example request
```
api.tasqinc.com/v1/profile/{user_email}
```
Example response
```
{
    "username": "tasq@tasqinc.com",
    "user_id": "8e69e0b9-4e2f-4b8b-97e4-2c107be4d99d",
    "accepting_tasqs": true,
    "teams": [
        "Team_1"
    ],
    "user_phone_number": "+13035555555"
}
```

`200`: Returned if the request is successful.
`401`: Returned if the authentication credentials are incorrect or missing.
`403`: Returned if the user is not an administrator.
`404`: Returned if the role is not found.




*PUT /v1/profile*

Updates user profile.

**Request**
*BODY PARAMETERS*
username: String `REQUIRED`
Roles: Array
PhoneNumber: String
AcceptingTasqs: Boolean
Team: Array


Example request
```
{
  "username":"john@tasqinc.com",
  "PhoneNumber":"+13035555555",
  "AcceptingTasqs":true,
  "Team":["Team_1"]
}
```
Example response
```
{
  "Username": {username},
  "Error": False,
  "Success": True
}
```

`200`: Returned if the request is successful.
`401`: Returned if the authentication credentials are incorrect or missing.
`403`: Returned if the user is not an administrator.
`404`: Returned if the role is not found.
