from protorpc import messages


class ListBlueprintsRequest(messages.Message):
  pass


class ListBlueprintsResponse(messages.Message):
  content = messages.StringField(1)
#  blueprints = messages.MessageField(blueprint_messages.BlueprintMessages
  pass
