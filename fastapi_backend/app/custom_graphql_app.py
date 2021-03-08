from starlette.graphql import GraphQLApp
from starlette import status
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from graphql.error import format_error as format_graphql_error

# Why this class exists:
# See: https://stackoverflow.com/questions/65974026/fastapi-graphql-getting-error-nonetype-is-callable-when-raise-exception
# See: https://github.com/graphql-python/graphene/issues/1127
# See: https://github.com/graphql-python/graphene/issues/1312
# See: https://github.com/encode/starlette/issues/619
class CustomGraphQLApp(GraphQLApp):
    # Override current method
    async def handle_graphql(self, request: Request) -> Response:
        if request.method in ("GET", "HEAD"):
            if "text/html" in request.headers.get("Accept", ""):
                if not self.graphiql:
                    return PlainTextResponse(
                        "Not Found", status_code=status.HTTP_404_NOT_FOUND
                    )
                return await self.handle_graphiql(request)

            data = request.query_params  # type: typing.Mapping[str, typing.Any]

        elif request.method == "POST":
            content_type = request.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = await request.json()
            elif "application/graphql" in content_type:
                body = await request.body()
                text = body.decode()
                data = {"query": text}
            elif "query" in request.query_params:
                data = request.query_params
            else:
                return PlainTextResponse(
                    "Unsupported Media Type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

        else:
            return PlainTextResponse(
                "Method Not Allowed", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")
        except KeyError:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        background = BackgroundTasks()
        context = {"request": request, "background": background}

        result = await self.execute(
            query, variables=variables, context=context, operation_name=operation_name
        )
        error_data = (
            [format_graphql_error(err) for err in result.errors]
            if result.errors
            else None
        )
        response_data = {"data": result.data}
        if error_data:
            response_data["errors"] = error_data
        status_code = (
            status.HTTP_400_BAD_REQUEST if result.errors else status.HTTP_200_OK
        )

        return JSONResponse(
            response_data, status_code=status_code, background=background
        )
