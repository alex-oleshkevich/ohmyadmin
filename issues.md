# FEATURES
1. implement relations
5. add profile settings (change name, reset password)
6. permissions & access control
7. improve ui
8. improve Customer display page -> need components to display nested items
9. remove colspan from components -> introduce Container component
10. table object actions as buttons + row actions builder
11. file uploads
12. search in joined tables
13. order by joined tables
14. global search
16. actions should have static urls - pass route name and path prefix via args
18. simplify datasource -> django-like?
19. implement table component and use in TableView. just like display view
20. django-like filters for sqla datasource
22. user menu builder
23. global actions
24. pass welcome screen as argument of app
25. Builder in display view: `DisplayField(builder=lambda r, o: components.Link(url=r.url_for('/')))`
26. move searchable and sortable field list to datasource
27. report error toast if request fails with 500
28. display fields to be components. ideally like this
```python
display_view = display_view_builder(builder=lambda r, o: Column(children=[
    DisplayField(label='name', value=o.name),
    DisplayField(label='name', value=o.name, component=Badge(o.name)),
    Row(children=[
        DisplayField(),
        DisplayField(),
    ]),
]))
```
