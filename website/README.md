# 网站维护与部署

网站使用 MkDocs 与 Material 主题，由仓库中的 Markdown 生成。课程、题目和资料仍在原目录维护，GitHub 上的原有阅读路径保持可用。

`scripts/prepare_site.py` 将公开内容整理到 `.site-src/`，其中各级 `README.md` 映射为 `index.md`；MkDocs 根据根目录的 `mkdocs.yml` 构建到 `site/`。`.site-src/`、`site/` 都是生成产物，修改内容时编辑原 Markdown，再重新准备与构建。`website/` 保存网站样式和维护说明，本页不进入学习站点。

## 本地预览

在仓库根目录使用 Python 3.12 创建独立环境：

```bash
python3.12 -m venv .venv-docs
source .venv-docs/bin/activate
python -m pip install -r requirements-docs.txt
python scripts/prepare_site.py
python -m mkdocs serve
```

打开命令输出的本地地址。修改原 Markdown 后，重新运行 `python scripts/prepare_site.py`，让预览读取最新内容。

提交前执行与 CI 相同的检查：

```bash
python scripts/check_repo.py
python -m unittest discover -s tests -v
python scripts/prepare_site.py
python -m mkdocs build --strict
python scripts/check_site.py
```

构建完成后，静态文件位于 `site/`。依赖的固定版本见 [requirements-docs.txt](../requirements-docs.txt)；更新版本时，同时检查导航、中文搜索、题目折叠和移动端阅读。

## GitHub Pages

在仓库 **Settings → Pages → Build and deployment** 中，将 **Source** 设为 **GitHub Actions**。默认访问地址为：

[https://harrytted.github.io/ai-agent-interview-playbook/](https://harrytted.github.io/ai-agent-interview-playbook/)

[Pages 工作流](../.github/workflows/pages.yml) 在推送到 `main` 或手动运行时构建；仅 `main` 的成功构建会上传并部署。Pull Request 执行内容检查、测试与严格构建，用于合并前验证。需要手动发布时，在 **Actions → Documentation site → Run workflow** 选择 `main`。

构建任务只读取仓库，部署任务单独获得 Pages 与 OIDC 权限，并使用 `github-pages` 环境。部署按 `pages` 并发组串行执行，正在进行的部署不会因新构建被取消。部署成功后可从工作流的环境链接打开实际地址；更换仓库名或域名时，同步更新 `mkdocs.yml` 的 `site_url`。

## 维护入口

- [MkDocs 配置](../mkdocs.yml)：导航、主题和 Markdown 扩展。
- [内容准备脚本](../scripts/prepare_site.py)：公开内容范围、目录映射与站内链接转换。
- [贡献指南](../CONTRIBUTING.md)：内容修改与验证约定。
- [GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)：部署权限、产物与环境的官方说明。

内容源与站点配置分开维护；调整主题或迁移生成器时，先复用原 Markdown，再检查链接、搜索、折叠及样式。
