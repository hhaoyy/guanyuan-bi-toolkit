#!/usr/bin/env python3
"""Inspect a skill installation or initialize a private dashboard project."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from package_info import inspect_bundle, inspect_skill

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SKILLS_DIR = SKILL_DIR.parent
TEMPLATES = {'overview': ['orders', 'sales'], 'funnel': ['visitors', 'leads', 'orders'],
             'channels': ['visitors', 'orders', 'sales'], 'monitor': ['sales']}
COMPONENTS = ['guancli', 'guands', 'guanvis', 'guanetl', 'guanwf', 'guanmetric']


def project_check(project):
    project = Path(project)
    try:
        data = json.loads((project / 'project.json').read_text(encoding='utf-8'))
        if data.get('schema') != 1 or data.get('template') not in TEMPLATES:
            raise ValueError('Unsupported project schema')
        required = ['field-mapping.json', 'src/index.html', 'src/data.js', 'src/dashboard.js',
                    'src/engine.js', 'src/view.js', 'src/theme.css']
        missing = [name for name in required if not (project / name).is_file()]
        return {'status': 'ready' if not missing else 'incomplete', 'missing': missing,
                'toolkit_version': data.get('toolkit_version'),
                'scope': 'Project structure only; data bindings and platform acceptance are untested.'}
    except (OSError, ValueError, TypeError):
        return {'status': 'unrecognized', 'next': 'Inspect project.json locally; existing files were not changed.'}


def check(skills_dir, components=None, bin_dir=None, project=None):
    report = inspect_bundle(skills_dir)
    report['checked_skills_dir'] = str(Path(skills_dir).resolve())
    report['invoked_skill_dir'] = str(SKILL_DIR)
    report['scope'] = 'Local files and optional CLI startup; no login, data queries or publication.'
    report['next'] = 'If the agent loads a different directory, check that directory explicitly.'
    if components:
        if report['skills']['guanyuan-cli']['status'] != 'ready':
            report['cli'] = {'status': 'blocked', 'reason': 'Resolve the CLI skill integrity issue first.'}
            report['status'] = 'needs_attention'
        else:
            script = Path(skills_dir) / 'guanyuan-cli/scripts/compatibility.py'
            spec = importlib.util.spec_from_file_location('toolkit_compatibility', script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            report['cli'] = {name: module.probe(name, bin_dir) for name in dict.fromkeys(components)}
            report['runtime_selection'] = str(Path(bin_dir).resolve()) if bin_dir else 'PATH'
            if any(r['status'] != 'ready' for r in report['cli'].values()):
                report['status'] = 'needs_attention'
    if project:
        report['project'] = project_check(project)
        if report['project']['status'] != 'ready':
            report['status'] = 'needs_attention'
    return report


def initialize(project, template, skills_dir=DEFAULT_SKILLS_DIR):
    project = Path(project).expanduser()
    if project.is_symlink():
        raise ValueError('Project destination is a symbolic link; choose an explicit new directory.')
    project = project.resolve()
    # Never create private work inside a public checkout or installed skills.
    skills_dir = Path(skills_dir).resolve()
    package_root = skills_dir.parent if (skills_dir.parent / 'VERSION').is_file() else skills_dir
    if project == package_root or package_root in project.parents or project in package_root.parents:
        raise ValueError('Create the project outside the toolkit package and installed skills.')
    if project.exists() and any(project.iterdir()):
        if (project / 'project.json').is_file():
            result = project_check(project)
            return {'status': 'existing', 'changed': False, 'project': str(project), 'check': result}
        raise ValueError('Destination is not empty. Choose a new project subdirectory; no files were changed.')
    if template not in TEMPLATES:
        raise ValueError('Unknown template')
    for name in ['guanyuan-bi', 'guanyuan-html-bi-generic']:
        if inspect_skill(skills_dir / name)['status'] != 'ready':
            raise ValueError('Resolve skill integrity issues before initializing a project.')
    version = inspect_skill(skills_dir / 'guanyuan-bi')['version']
    if inspect_skill(skills_dir / 'guanyuan-html-bi-generic')['version'] != version:
        raise ValueError('Install matching skill versions before initializing a project.')
    manifest = {'schema': 1, 'toolkit_version': version, 'template': template, 'status': 'initialized',
                'source': 'src/', 'field_mapping': 'field-mapping.json',
                'platform': {'instance': None, 'page_id': None, 'dataset_bindings': []},
                'runtime': {'bin_dir': None, 'versions': {}},
                'acceptance': {'local_preview': 'pending', 'platform_publish': 'pending', 'same_id_update': 'pending'},
                'evidence_directory': 'evidence/'}
    fields = {'period': {'source': None, 'values': ['baseline', 'current']}, 'group': {'source': None}}
    fields.update({name: {'source': None, 'unit': None, 'definition': None} for name in TEMPLATES[template]})
    mapping = {'schema': 1, 'grain': ['period', 'group'], 'fields': fields,
               'comparison': {'baseline': None, 'current': None, 'timezone': None},
               'quality_evidence': {'refresh_watermark': None, 'complete_windows': None, 'unique_grain': None},
               'note': 'Confirm definitions and evidence before setting qualityConfirmed in src/data.js.'}
    project.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.guanyuan-project-', dir=project.parent) as temporary:
        stage = Path(temporary) / 'project'
        (stage / 'src').mkdir(parents=True)
        (stage / 'evidence').mkdir()
        (stage / 'project.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (stage / 'field-mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (stage / '.gitignore').write_text('evidence/\nlocal/\n.env\n.env.*\n*.har\n', encoding='utf-8')
        (stage / 'README.md').write_text('''# 你的观远看板工程

打开 `src/index.html` 查看页面。初始工程没有数据，不会生成业务结论。

继续向 guanyuan-bi 提供字段说明或已有看板链接，让它：
1. 填写 field-mapping.json 中的字段、单位、粒度和比较范围。
2. 编写字段适配并更新 src/data.js；只有核实质量证据后才启用分析。
3. 先完成本地预览，再按当前官方 CLI 文档构建平台工程，移除本地数据加载器。
4. 将实际页面编号、数据集绑定和 CLI 版本记入 project.json；验收证据存入 evidence/。

后续修改从本工程继续，先比对线上状态，再复用原看板编号。不要把初始化状态写成已发布。
此工程可能包含组织数据与资源信息，请保存在获准的私有位置；gitignore 不替代发布审阅。
''', encoding='utf-8')
        for filename in ['engine.js', 'view.js', 'theme.css']:
            shutil.copyfile(skills_dir / 'guanyuan-html-bi-generic/assets/templates' / filename, stage / 'src' / filename)
        context = {'currentLabel': '', 'baselineLabel': '', 'unit': '', 'qualityConfirmed': False,
                   'cohortConfirmed': False, 'threshold': None, 'evidenceLabel': '尚未接入数据'}
        (stage / 'src/data.js').write_text('window.BI_PROJECT = ' + json.dumps(
            {'template': template, 'rows': [], 'context': context}, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
        (stage / 'src/dashboard.js').write_text("const p = window.BI_PROJECT;\nBITemplateView.mount(document.getElementById('preview'), p.template, p.rows, p.context);\n", encoding='utf-8')
        (stage / 'src/index.html').write_text('''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>我的观远看板工程</title><link rel="stylesheet" href="theme.css">
<body style="margin:24px;font-family:system-ui,sans-serif"><h1>看板工程已创建</h1>
<p>请让 AI 根据字段说明完成映射和预览，再接入观远。工程步骤见 README.md。</p>
<div id="preview"></div><script src="engine.js"></script><script src="view.js"></script>
<script src="data.js"></script><script src="dashboard.js"></script></body></html>
''', encoding='utf-8')
        if project.exists():
            project.rmdir()  # Only a still-empty directory can be replaced.
        os.replace(stage, project)
    return {'status': 'initialized', 'version': version, 'project': str(project),
            'preview': str(project / 'src/index.html'), 'next': 'Provide field definitions to guanyuan-bi and continue in this project.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('version')
    inspect = commands.add_parser('check')
    inspect.add_argument('--skills-dir', type=Path, default=DEFAULT_SKILLS_DIR)
    inspect.add_argument('--components', nargs='+', choices=COMPONENTS)
    inspect.add_argument('--bin-dir', type=Path)
    inspect.add_argument('--project', type=Path)
    init = commands.add_parser('init')
    init.add_argument('--project', type=Path, required=True)
    init.add_argument('--template', choices=list(TEMPLATES), default='overview')
    args = parser.parse_args()
    try:
        if args.command == 'version':
            result = inspect_skill(SKILL_DIR)
        elif args.command == 'check':
            result = check(args.skills_dir, args.components, args.bin_dir, args.project)
        else:
            result = initialize(args.project, args.template)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == 'init':
            return 0 if result['status'] == 'initialized' or result.get('check', {}).get('status') == 'ready' else 1
        return 0 if result['status'] == 'ready' else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'error', 'message': str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
