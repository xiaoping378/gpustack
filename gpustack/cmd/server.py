import argparse
import asyncio
import multiprocessing

from gpustack.agent.agent import Agent
from gpustack.agent.config import AgentConfig
from gpustack.server.server import Server
from gpustack.server.config import ServerConfig
from gpustack.utils import get_first_non_loopback_ip


def setup_server_cmd(subparsers: argparse._SubParsersAction):
    parser_server: argparse.ArgumentParser = subparsers.add_parser(
        "server", help="Run management server.", description="Run management server."
    )
    group = parser_server.add_argument_group("Basic settings")
    group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode.",
        default=True,
    )
    group.add_argument(
        "--disable-agent",
        action="store_true",
        help="Disable embedded agent.",
        default=False,
    )
    group.add_argument(
        "--serve-default-models",
        action="store_true",
        help="Serve default models on bootstrap.",
        default=True,
    )
    group.add_argument(
        "--metrics-port",
        type=int,
        help="Port to expose metrics on, works when agent is enabled value isn't -1.",
        default=10051,
    )

    group = parser_server.add_argument_group("Node settings")
    group.add_argument(
        "--node-ip",
        type=str,
        help="IP address of the node. Auto-detected by default.",
    )

    group = parser_server.add_argument_group("Data settings")
    group.add_argument(
        "--data-dir",
        type=str,
        help="Directory to store data. Default is OS specific.",
    )
    group.add_argument(
        "--database-url",
        type=str,
        help="URL of the database. Example: postgresql://user:password@hostname:port/db_name",
    )

    parser_server.set_defaults(func=run_server)


def run_server(args):
    server_cfg = to_server_config(args)
    sub_processes = []

    if not server_cfg.disable_agent:
        agent_cfg = AgentConfig(
            server="http://127.0.0.1",
            node_ip=server_cfg.node_ip,
            debug=server_cfg.debug,
            metric_enabled=server_cfg.metric_enabled,
            metrics_port=server_cfg.metrics_port,
        )
        agent = Agent(agent_cfg)
        agent_process = multiprocessing.Process(target=agent.start, args=(True,))
        sub_processes = [agent_process]

    server = Server(config=server_cfg, sub_processes=sub_processes)

    asyncio.run(server.start())


def to_server_config(args) -> ServerConfig:
    cfg = ServerConfig()
    if args.serve_default_models:
        cfg.serve_default_models = args.serve_default_models

    if args.debug:
        cfg.debug = args.debug

    if args.disable_agent:
        cfg.disable_agent = args.disable_agent
    else:
        cfg.metric_enabled = args.metrics_port != -1
        cfg.metrics_port = args.metrics_port

    if args.node_ip:
        cfg.node_ip = args.node_ip
    else:
        cfg.node_ip = get_first_non_loopback_ip()

    if args.data_dir:
        cfg.data_dir = args.data_dir

    if args.database_url:
        cfg.database_url = args.database_url
    else:
        cfg.database_url = f"sqlite:///{cfg.data_dir}/database.db"

    return cfg
