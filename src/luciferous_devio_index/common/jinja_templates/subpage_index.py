TEMPLATE_SUBPAGE_INDEX = """
<!DOCTYPE html>
<html lang="ja-jp">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>Index of /{{ path }}</title>
    <style>
        th {
            border-bottom: 1px solid black;
        }
        th, td {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        table {
            border-collapse: collapse;
        }
    </style>
</head>
<body>
<h2>Index of /{{ path }}</h2>
<table>
    <thead>
    <tr>
        <th>name</th>
        <th>last modified</th>
        <th>size</th>
    </tr>
    </thead>
    <tbody>
    <tr>
        <td><a href="..">../</a></td>
        <td></td>
        <td></td>
    </tr>
    {% for item in contents %}
    <tr>
        <td><a href="{{ item.name }}">{{item.name}}</a></td>
        <td>{{ item.last_modified_at }}</td>
        <td>{{ item.size }}</td>
    </tr>
    {% endfor %}
    </tbody>
</table>
</body>
</html>
"""
