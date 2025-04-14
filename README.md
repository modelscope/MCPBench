# MCPBench

MCPBench is an evaluation framework for MCP Server. It supports the evaluation of two types of servers: Web Search and Database Query, and is compatible with both local and remote MCP Servers. The framework primarily evaluates different MCP Servers (such as Brave Search, DuckDuckGo, etc.) in terms of task completion accuracy, latency, and token consumption under the same LLM and Agent configurations. 

Here is the [evaluation report](https://github.com/modelscope/MCPBench/blob/main/mcpbench.pdf) .

The implementation is based on [LangProBe: a Language Programs Benchmark](https://arxiv.org/abs/2502.20315).

# Installation

The framework requires Python version >= 3.11, nodejs and jq.

```bash
conda create -n mcpbench python=3.11 -y
conda activate mcpbench
pip install -r requirements.txt
```

# Quick Usage
## LLM Configuration
Prepare the LLM key and endpoint in your environment variables:
```bash
export MODEL_KEY=your_api_key_here
export MODEL_ENDPOINT=your_model_endpoint_here
```

## Launch MCP Server
### Launch stdio MCP as SSE
If the MCP does not support SSE, write the config like:
```json
{
  "name": "DuckDuckGo",
  "command": "uvx duckduckgo-mcp-server",
  "args": "",
  "port": 8001,
  "tool_name": "search",
  "tool_keyword": "query"
}
```

Save this config file in the `configs` folder and launch it using:

```bash
sh launch_mcp_as_sse.sh YOUR_CONFIG_FILE
```

For example, if the config file is duckduckgo.json, then run:
```bash
sh launch_mcp_as_sse.sh duckduckgo.json
```

### Launch SSE MCP
If your server supports SSE, you can use it directly. The URL will be http://localhost:8001/sse

For SSE-supported MCP Server, write the config like:
```json
{
  "name": "Exa Search",
  "command": "",
  "args": "",
  "url": "https://mcp-a11aaa67-0a82-40a2.api-inference.modelscope.cn/sse",
  "port": 0,
  "tool_name": "web_search",
  "tool_keyword": "query"
}
```

## Launch Evaluation
To evaluate the MCP Server's performance on Web Search tasks:
```bash
sh evaluation_websearch.sh YOUR_CONFIG_FILE
```

To evaluate the MCP Server's performance on Database Query tasks:
```bash
sh evaluation_db.sh YOUR_CONFIG_FILE
```

# Datasets and Experimental Results
Our framework provides two datasets for evaluation. For the WebSearch task, the dataset is located at `MCPBench/langProBe/WebSearch/data/frames_test.jsonl`, containing 200 QA pairs each from [Frames](https://arxiv.org/abs/2409.12941), news, and technology domains. Our framework for automatically constructing evaluation datasets will be open-sourced later.

For the Database Query task, the dataset is located at `MCPBench/langProBe/DB/data/car_bi.jsonl`. You can add your own dataset in the following format:

```json
{
  "unique_id": "",
  "Prompt": "",
  "Answer": ""
}
```

We have evaluated mainstream MCP Servers on both tasks. For detailed experimental results, please refer to `results.md`

# Citation
If you find this work useful, please consider citing our project:

```bibtex
@misc{mcpbench,
  title={MCPBench: A Benchmark for Evaluating MCP Servers},
  author={Zhiling Luo,Xiaorong Shi, Xuanrui Lin, Yang Jin,Bolin Ding},
  howpublished = {\url{https://github.com/modelscope/MCPBench}},
  year={2025}
}
```
