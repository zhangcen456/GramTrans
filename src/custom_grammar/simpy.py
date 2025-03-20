def simpy_transforms(new_grammar):
    #grammar update for simpy that can not be automated
    new_grammar['decorator']={
      "type": "SEQ",
      "members": [
        {
          "type": "STRING",
          "value": "@"
        },
        {
          "type": "SYMBOL",
          "name": "expression"
        },
        {
          "type": "CHOICE",
          "members": [
            {
              "type": "CHOICE",
              "members": [
                {
                  "type": "STRING",
                  "value": "<line_sep>"
                },
                {
                  "type": "SYMBOL",
                  "name": "comment"
                }
              ]
            },
            {
              "type": "BLANK"
            }
          ]
        }
      ]
    }#choice(line_sep,comment)
    new_grammar['_suite']['members']=[new_grammar['_suite']['members'][1]]#delete choice
    new_grammar['_match_block']['members']=[{
          "type": "SEQ",
          "members": [
            {
              "type": "STRING",
              "value": "<block_start>"
            },
            {
              "type": "REPEAT",
              "content": {
                "type": "FIELD",
                "name": "alternative",
                "content": {
                  "type": "SYMBOL",
                  "name": "case_clause"
                }
              }
            },
            {
              "type": "CHOICE",
              "members": [
                {
                  "type": "STRING",
                  "value": "<line_sep>"
                },
                {
                  "type": "BLANK"
                }
              ]
            },
            {
              "type": "STRING",
              "value": "<block_end>"
            }
          ]
        }]#delete choice
    new_grammar['_group_statements']={
      "type":"SEQ",
      "members":[
        {
          "type": "SEQ",
          "members": [
            {
              "type": "SYMBOL",
              "name": "_statement"
            },
            {
              "type": "REPEAT",
              "content": {
                "type": "SEQ",
                "members": [
                  {
                    "type": "CHOICE",
                    "members":[
                      {
                        "type":"STRING",
                        "value":"<line_sep>"
                      },
                      {
                        "type":"SYMBOL",
                        "name":"comment"
                      }
                    ]
                  },
                  {
                    "type": "SYMBOL",
                    "name": "_statement"
                  }
                ]
              }
            }
          ]
        },
        {
          "type":"CHOICE",
          "members":[
            {
              "type":"SYMBOL",
              "name":"comment"
            },
            {
              "type":"BLANK"
            }
          ]
        }
      ]
    }
    new_grammar['block']['members'][1]['members'][0]={
          "type": "SYMBOL",
          "name":"_group_statements"
        }
    new_grammar['module']={
      "type": "SYMBOL",
      "name": "_group_statements"
    }
    new_grammar['function_definition']['members'][4]={
          "type": "FIELD",
          "name": "parameters",
          "content": {
            "type": "CHOICE",
            "members": [
              {
                "type": "ALIAS",
                "content": {
                  "type": "SYMBOL",
                  "name": "_parameters"
                },
                "named": True,
                "value": "parameters"
              },
              {
                "type": "BLANK"
              }
            ]
          }
        }