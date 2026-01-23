FROM node:20

ARG TZ
ENV TZ="$TZ"

ARG CLAUDE_CODE_VERSION=latest

# Install basic development tools and iptables/ipset
RUN apt-get update && apt-get install -y --no-install-recommends \
  less \
  git \
  procps \
  sudo \
  fzf \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  iptables \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  jq \
  nano \
  vim \
  curl \
  wget \
  python3 \
  python3-pip \
  shellcheck \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Terraform
ARG TERRAFORM_VERSION=1.14.3
RUN ARCH=$(dpkg --print-architecture) && \
  wget -O terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" && \
  unzip terraform.zip && \
  mv terraform /usr/local/bin/ && \
  rm terraform.zip && \
  terraform version

# Install gcloud CLI (for GCP operations)
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
  tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
  gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
  apt-get update && apt-get install -y google-cloud-cli && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Install kubectl (for Kubernetes operations)
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
  install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
  rm kubectl && \
  kubectl version --client

# Install tflint (Terraform linter)
ARG TFLINT_VERSION=0.55.1
RUN ARCH=$(dpkg --print-architecture) && \
  if [ "$ARCH" = "amd64" ]; then TFLINT_ARCH="amd64"; else TFLINT_ARCH="arm64"; fi && \
  wget "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_${TFLINT_ARCH}.zip" && \
  unzip tflint_linux_${TFLINT_ARCH}.zip && \
  mv tflint /usr/local/bin/ && \
  rm tflint_linux_${TFLINT_ARCH}.zip && \
  tflint --version

# Install terraform-docs (documentation generator)
ARG TERRAFORM_DOCS_VERSION=0.19.0
RUN ARCH=$(dpkg --print-architecture) && \
  if [ "$ARCH" = "amd64" ]; then TFDOCS_ARCH="amd64"; else TFDOCS_ARCH="arm64"; fi && \
  wget "https://github.com/terraform-docs/terraform-docs/releases/download/v${TERRAFORM_DOCS_VERSION}/terraform-docs-v${TERRAFORM_DOCS_VERSION}-linux-${TFDOCS_ARCH}.tar.gz" && \
  tar -xzf terraform-docs-v${TERRAFORM_DOCS_VERSION}-linux-${TFDOCS_ARCH}.tar.gz && \
  mv terraform-docs /usr/local/bin/ && \
  rm terraform-docs-v${TERRAFORM_DOCS_VERSION}-linux-${TFDOCS_ARCH}.tar.gz && \
  terraform-docs --version

# Install yq (YAML processor - complement to jq)
ARG YQ_VERSION=4.44.6
RUN ARCH=$(dpkg --print-architecture) && \
  if [ "$ARCH" = "amd64" ]; then YQ_ARCH="amd64"; else YQ_ARCH="arm64"; fi && \
  wget "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_${YQ_ARCH}" -O /usr/local/bin/yq && \
  chmod +x /usr/local/bin/yq && \
  yq --version

# Install gitleaks (secret scanner)
ARG GITLEAKS_VERSION=8.22.1
RUN ARCH=$(dpkg --print-architecture) && \
  if [ "$ARCH" = "amd64" ]; then GITLEAKS_ARCH="x64"; else GITLEAKS_ARCH="arm64"; fi && \
  wget "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_${GITLEAKS_ARCH}.tar.gz" && \
  tar -xzf gitleaks_${GITLEAKS_VERSION}_linux_${GITLEAKS_ARCH}.tar.gz && \
  mv gitleaks /usr/local/bin/ && \
  rm gitleaks_${GITLEAKS_VERSION}_linux_${GITLEAKS_ARCH}.tar.gz && \
  gitleaks version

# Install bat (better cat with syntax highlighting)
ARG BAT_VERSION=0.24.0
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/sharkdp/bat/releases/download/v${BAT_VERSION}/bat_${BAT_VERSION}_${ARCH}.deb" && \
  dpkg -i bat_${BAT_VERSION}_${ARCH}.deb && \
  rm bat_${BAT_VERSION}_${ARCH}.deb && \
  bat --version

# Install ripgrep (faster grep)
ARG RIPGREP_VERSION=14.1.1
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/BurntSushi/ripgrep/releases/download/${RIPGREP_VERSION}/ripgrep_${RIPGREP_VERSION}-1_${ARCH}.deb" && \
  dpkg -i ripgrep_${RIPGREP_VERSION}-1_${ARCH}.deb && \
  rm ripgrep_${RIPGREP_VERSION}-1_${ARCH}.deb && \
  rg --version

# Install pre-commit (git hooks framework)
RUN pip3 install --no-cache-dir pre-commit && \
  pre-commit --version

# Ensure default node user has access to /usr/local/share
RUN mkdir -p /usr/local/share/npm-global && \
  chown -R node:node /usr/local/share

ARG USERNAME=node

# Persist bash history.
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && mkdir /commandhistory \
  && touch /commandhistory/.bash_history \
  && chown -R $USERNAME /commandhistory

# Set `DEVCONTAINER` environment variable to help with orientation
ENV DEVCONTAINER=true

# Create workspace and config directories and set permissions
RUN mkdir -p /workspace /home/node/.claude && \
  chown -R node:node /workspace /home/node/.claude

WORKDIR /workspace

ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  sudo dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# Set up non-root user
USER node

# Install global packages
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Set the default shell to zsh rather than sh
ENV SHELL=/bin/zsh

# Set the default editor and visual
ENV EDITOR=nano
ENV VISUAL=nano

# Default powerline10k theme
ARG ZSH_IN_DOCKER_VERSION=1.2.0
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# Install Claude
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}


# Copy and set up firewall script
COPY init-firewall.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/init-firewall.sh && \
  echo "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/node-firewall && \
  chmod 0440 /etc/sudoers.d/node-firewall
USER node

# now we add these things for our node user in our container
# add uv for our python work
RUN wget -qO- https://astral.sh/uv/install.sh | sh