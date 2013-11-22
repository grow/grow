from protorpc import messages


class DeploymentKind(messages.Enum):
  GOOGLE_STORAGE = 1
  GOOGLE_STORAGE_FROM_APP_ENGINE = 2
  AMAZON_S3 = 3
  GROW_CHANNEL = 4
  FILE_SYSTEM = 5
