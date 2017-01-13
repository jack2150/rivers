/**
 * Created by jack on 12/29/2016.
 */
function base_ui() {
  webix.ui({
    container: "base_div",
    id: "layout",
    css: "base-content",
    rows: [
      {type: "header", content: "site-header"},
      {content: "nav-global", height: 24},

      {
        cols: [
          menu,
          {
            rows: [
              {content: "breadcrumbs", height: 30},
              {
                cols: [
                  {
                    scroll: "y",
                    rows: [
                      {view: "template", content: "page-title", type: "header"},
                      {view: "template", content: "content", scroll: "y"}
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }).show();
}

var menu = {
  view: "menu", id: "m1",
  layout: "y",
  width: 300,
  minWidth: 50,
  maxWidth: 250,
  select: true,
  data: [
    {id: "1", value: "Translations", icon: "qrcode", badge: 20},
    {id: "2", value: "Posts", icon: "file-word-o", badge: 3},
    {$template: "Spacer"},
    {id: "3", value: "Help", icon: "support"},
    {id: "4", value: "Info", icon: "info-circle"},
    {id: "5", value: "About", icon: "question-circle"}
  ],
  on: {
    onMenuItemClick: function (id) {
      $$("t1").setHTML("Click: " + this.getMenuItem(id).value);
    }
  }
};

function index_ui() {
  webix.ui({
    container: "content-main",
    id: "content",
    borderless: true,
    type: "clean",
    cols: [
      {
        content: "content-index",
        width: 410
      },
      {
        type: "template", width: 10
      },
      {
        content: "content-related",
        width: 310
      },
      {
        type: "template", width: 10
      },
      {
        content: "custom_view"

      }
    ]
  }).show();
}

function list_ui(log_data, container, title, height, template) {
  webix.ui({
    container: container,
    width: 300,
    height: 400,
    rows: [
      {
        view: "template", template: title,
        height: 32, type: "section"
      },
      {
        view: "list",
        template: template,
        type: {
          height: height
        },
        data: log_data
      }
    ]
  }).show();
}

var content = {
  container: "content-div",
  rows: [
    {view: "template", template: "{% if title %}{{ title }}{% endif %}", type: "header"},
    {view: "template", content: "content-main"}
  ]
};