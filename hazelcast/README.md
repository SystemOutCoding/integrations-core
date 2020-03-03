# Agent Check: Hazelcast

## Overview

This check monitors [Hazelcast][1].

## Setup

### Installation

The Hazelcast check is included in the [Datadog Agent][2] package.
No additional installation is needed on your server.

### Configuration

1. Edit the `hazelcast.d/conf.yaml` file, in the `conf.d/` folder at the root of your
   Agent's configuration directory to start collecting your hazelcast performance data.
   See the [sample hazelcast.d/conf.yaml][2] for all available configuration options.

   This check has a limit of 350 metrics per instance. The number of returned metrics is indicated in the info page.
   You can specify the metrics you are interested in by editing the configuration below.
   To learn how to customize the metrics to collect visit the [JMX Checks documentation][3] for more detailed instructions.
   If you need to monitor more metrics, contact [Datadog support][4].

2. [Restart the Agent][5]

### Validation

[Run the Agent's `status` subcommand][6] and look for `hazelcast` under the Checks section.

## Data Collected

### Metrics

Hazelcast does not include any metrics.

### Service Checks

Hazelcast does not include any service checks.

### Events

Hazelcast does not include any events.

## Troubleshooting

Need help? Contact [Datadog support][4].


[1]: **LINK_TO_INTEGERATION_SITE**
[2]: https://github.com/DataDog/integrations-core/blob/master/hazelcast/datadog_checks/hazelcast/data/conf.yaml.example
[3]: https://docs.datadoghq.com/integrations/java
[4]: https://docs.datadoghq.com/help
[5]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[6]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
