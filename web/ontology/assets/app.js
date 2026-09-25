/* Read-only projection. The fetched snapshot remains the only data authority. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const state = { snapshot: null, bytes: null, nodes: new Map(), sources: new Map(), tasks: new Map(), checkpoints: new Map(), selected: null, tab: 'definition', search: '', expanded: new Set(), unknown: null, loading: false, focusedTask: null, focusedCheckpoint: null };
  const element = (tag, className, text) => { const item = document.createElement(tag); if (className) item.className = className; if (text !== undefined) item.textContent = String(text); return item; };
  const append = (parent, ...children) => { children.filter(Boolean).forEach(child => parent.appendChild(child)); return parent; };
  const button = (text, className, handler) => { const item = element('button', className, text); item.type = 'button'; item.addEventListener('click', handler); return item; };
  const pretty = value => String(value ?? 'Not declared').replaceAll('_', ' ');
  const compactHash = value => typeof value === 'string' ? value.slice(0, 12) + '…' + value.slice(-8) : 'Not available';
  const nodeLabel = id => state.nodes.get(id)?.name || id;
  const list = value => Array.isArray(value) ? value : [];
  const badge = (value, extra = '') => element('span', 'badge ' + extra, pretty(value));
  const section = title => { const item = element('section', 'detail-section'); item.appendChild(element('h3', 'detail-title', title)); return item; };
  const empty = text => element('p', 'empty-detail', text);
  const announce = text => { $('announcement').textContent = text; };
  function hashNode() { return new URLSearchParams(location.hash.slice(1)).get('node'); }
  function navigate(id, updateHistory = true) {
    if (!state.snapshot) return;
    state.unknown = id && !state.nodes.has(id) ? id : null;
    state.selected = state.nodes.has(id) ? id : state.snapshot.root;
    const node = state.nodes.get(state.selected);
    list(node.path).forEach(parent => state.expanded.add(parent));
    if (updateHistory) history.pushState(null, '', '#node=' + encodeURIComponent(state.selected));
    renderTree(); renderSelected();
    announce('Selected ' + node.name);
  }
  function setTab(tab, focus = false) {
    state.tab = tab;
    document.querySelectorAll('[data-tab]').forEach(item => { const active = item.dataset.tab === tab; item.classList.toggle('active', active); item.setAttribute('aria-selected', String(active)); item.tabIndex = active ? 0 : -1; if (active && focus) item.focus(); });
    $('detail-content').setAttribute('aria-labelledby', 'tab-' + tab);
    renderDetails();
  }
  function portChip(node, port) {
    const item = button('', 'port-chip', () => { if (state.selected !== node.id) navigate(node.id); setTab('ports'); $('detail-content').scrollIntoView({ block: 'nearest' }); });
    item.setAttribute('aria-label', 'Inspect ' + node.name + ' port ' + port.id);
    append(item, element('span', 'port-dot'), element('span', '', port.id));
    item.title = port.protocol + ' · ' + port.unit;
    return item;
  }
  function matchingIds() {
    if (!state.search) return null;
    const found = new Set(); let matchCount = 0;
    for (const node of state.nodes.values()) {
      if ([node.id, node.name, node.description].join(' ').toLocaleLowerCase().includes(state.search)) {
        found.add(node.id); list(node.path).forEach(id => found.add(id)); matchCount++;
      }
    }
    $('search-summary').textContent = matchCount + (matchCount === 1 ? ' match' : ' matches');
    return found;
  }
  function renderTree() {
    const tree = $('tree'); tree.replaceChildren();
    if (!state.snapshot) return;
    const matches = matchingIds();
    if (!matches) $('search-summary').textContent = 'Containment';
    if (matches && !matches.size) { tree.appendChild(element('p', 'no-results', 'No membranes match “' + $('search').value + '”. Try a name, ID or description.')); return; }
    const build = (id, depth) => {
      const node = state.nodes.get(id); if (!node || (matches && !matches.has(id))) return null;
      const branch = element('li'); const row = element('div', 'tree-row' + (state.selected === id ? ' selected' : ''));
      row.style.paddingLeft = (depth * 13) + 'px';
      const children = list(node.children), isOpen = !!matches || state.expanded.has(id);
      const toggle = button(children.length ? (isOpen ? '−' : '+') : '', 'tree-toggle' + (!children.length ? ' empty' : ''), () => { if (state.expanded.has(id)) state.expanded.delete(id); else state.expanded.add(id); renderTree(); });
      toggle.setAttribute('aria-label', (isOpen ? 'Collapse ' : 'Expand ') + node.name);
      if (children.length) toggle.setAttribute('aria-expanded', String(isOpen)); else toggle.tabIndex = -1;
      if (matches) { toggle.disabled = true; toggle.title = 'Search keeps matching ancestors expanded'; }
      const select = button('', 'tree-select', () => navigate(id));
      if (state.selected === id) select.setAttribute('aria-current', 'true');
      select.title = node.name + ' · ' + node.id;
      append(select, element('span', 'tree-symbol' + (node.kind === 'connection' ? ' connection' : '')), element('span', '', node.name));
      append(row, toggle, select);
      if (list(node.gaps).length) { const gaps = element('span', 'tree-gaps', '·'); gaps.title = list(node.gaps).length + ' declared gaps'; row.appendChild(gaps); }
      branch.appendChild(row);
      if (children.length && isOpen) { const nested = element('ul', 'tree-list'); children.forEach(child => { const next = build(child, depth + 1); if (next) nested.appendChild(next); }); branch.appendChild(nested); }
      return branch;
    };
    const rootList = element('ul', 'tree-list'); rootList.appendChild(build(state.snapshot.root, 0)); tree.appendChild(rootList);
  }
  function compartment(node) {
    const item = element('div', 'compartment');
    const heading = element('div', 'compartment-head');
    append(heading, element('span', node.kind === 'connection' ? 'diamond' : 'tree-symbol'), button(node.name, 'node-link', () => navigate(node.id)), element('span', 'compartment-kind', pretty(node.kind)));
    append(item, heading, element('p', 'compartment-description', node.description));
    if (list(node.children).length) {
      const children = element('div', 'nested-contents');
      node.children.forEach(id => { const child = state.nodes.get(id); const link = button('', 'nested-child', () => navigate(id)); append(link, element('span', child.kind === 'connection' ? 'diamond' : 'tree-symbol'), document.createTextNode(child.name)); if (list(child.children).length) link.appendChild(element('span', '', String(child.children.length))); children.appendChild(link); });
      item.appendChild(children);
    }
    if (list(node.ports).length) { const ports = element('div', 'compartment-ports'); node.ports.forEach(port => ports.appendChild(portChip(node, port))); item.appendChild(ports); }
    return item;
  }
  function connectionRows(ids) {
    const rows = element('div', 'connection-list');
    ids.forEach(id => { const node = state.nodes.get(id); if (!node) return; const row = element('div', 'connection-row'); append(row, element('span', 'diamond'), button(node.name, 'node-link', () => { navigate(id); setTab('ports'); }), element('span', 'planned', node.connection_status || 'status undeclared')); rows.appendChild(row); });
    return rows;
  }
  function endpointPath(node) {
    const path = element('div', 'endpoint-path');
    list(node.endpoints).forEach((endpoint, index) => {
      const target = state.nodes.get(endpoint.node); const port = list(target?.ports).find(item => item.id === endpoint.port);
      if (index) path.appendChild(element('div', 'endpoint-join', 'port connection · ' + (node.connection_status || 'status undeclared')));
      const targetButton = button('', 'endpoint-button', () => { navigate(endpoint.node); setTab('ports'); });
      targetButton.setAttribute('aria-label', 'Open ' + nodeLabel(endpoint.node) + ', port ' + endpoint.port);
      append(targetButton, element('span', 'endpoint-label', 'Endpoint ' + (index + 1)), element('strong', '', nodeLabel(endpoint.node) + ' ↗'), element('code', '', endpoint.node + '.' + endpoint.port), element('small', '', (port?.protocol || 'Protocol not declared') + ' · ' + (port?.unit || 'Unit not declared')));
      path.appendChild(targetButton);
    });
    return path;
  }
  function renderSelected() {
    const node = state.nodes.get(state.selected); if (!node) return;
    const content = $('main-content'); content.replaceChildren();
    if (state.unknown) content.appendChild(element('p', 'unknown-warning', 'Unknown membrane ID “' + state.unknown + '”. Showing the root definition.'));
    const crumbs = element('nav', 'breadcrumbs'); crumbs.setAttribute('aria-label', 'Containment path');
    list(node.path).forEach((id, index) => { if (index) crumbs.appendChild(element('span', '', '/')); const item = button(nodeLabel(id), '', () => navigate(id)); if (id === node.id) item.setAttribute('aria-current', 'page'); crumbs.appendChild(item); });
    const eyebrow = element('div', 'node-eyebrow'); append(eyebrow, element('span', '', pretty(node.kind)), element('code', '', node.id));
    const title = element('h2', 'selected-heading', node.name); title.id = 'selected-title';
    append(content, crumbs, eyebrow, title, element('p', 'node-description', node.description));
    const toolbar = element('div', 'composition-toolbar'); append(toolbar, element('strong', '', node.kind === 'connection' ? 'Port relationship' : 'Inside this membrane'), element('span', '', list(node.children).length + ' contained · ' + list(node.ports).length + ' ports')); content.appendChild(toolbar);
    const shell = element('div', 'boundary-shell');
    const head = element('div', 'boundary-head'); append(head, element('span', 'boundary-name', node.name), element('span', 'boundary-tag', 'Boundary · ' + pretty(node.boundary?.binding)));
    append(shell, head, element('p', 'boundary-description', node.boundary?.description || 'No boundary description declared.'));
    if (list(node.ports).length) { const ports = element('div', 'boundary-ports'); node.ports.forEach(port => ports.appendChild(portChip(node, port))); shell.appendChild(ports); }
    if (node.kind === 'connection') shell.appendChild(endpointPath(node));
    if (list(node.children).length) { const children = element('div', 'compartments'); node.children.forEach(id => children.appendChild(compartment(state.nodes.get(id)))); shell.appendChild(children); }
    else if (node.kind !== 'connection') { const noChildren = element('div', 'no-children'); append(noChildren, element('strong', '', 'No contained membranes declared'), element('p', '', 'This definition has no authored children. Missing physical instances are recorded under Sources & gaps.')); shell.appendChild(noChildren); }
    content.appendChild(shell);
    const note = element('p', 'composition-note'); append(note, element('span', '', '↳'), element('span', '', node.kind === 'connection' ? 'A connection is a membrane with explicit endpoints. It does not change containment or qualify its physical binding.' : 'Containment describes composition. Matter ownership, physical parameters and validation stay explicit.')); content.appendChild(note);
    const connected = list(node.connections);
    if (connected.length) { const area = element('section', 'connection-section'); append(area, element('h3', 'section-label', 'Connected through ports'), connectionRows(connected)); content.appendChild(area); }
    if (list(node.gaps).length) { const link = button(list(node.gaps).length + (node.gaps.length === 1 ? ' declared gap' : ' declared gaps') + ' · inspect sources & gaps ↗', 'inline-link', () => { setTab('sources'); $('detail-content').scrollIntoView({ block: 'nearest' }); }); const area = element('div', 'connection-section'); area.appendChild(link); content.appendChild(area); }
    if (state.snapshot.plan) {
      const area = element('section', 'work-preview'); const primary = list(node.tasks).filter(task => task.ontology?.primary_membrane === node.id).length;
      append(area, element('h3', 'section-label', 'Work attached to this membrane'), element('p', 'detail-copy', primary + ' primary tasks · ' + (list(node.tasks).length - primary) + ' related tasks · ' + list(node.checkpoints).length + ' checkpoints'), button('Inspect work & verification ↗', 'inline-link', () => { setTab('work'); $('detail-content').scrollIntoView({ block: 'nearest' }); }), element('p', 'source-note', 'Planned requirements. Accepted evidence must be reconciled.'));
      content.appendChild(area);
    }
    $('inspector-kind').textContent = pretty(node.kind); renderDetails();
  }
  function fields(object, exclude = []) {
    const dl = element('dl', 'field-list');
    for (const [key, value] of Object.entries(object || {})) {
      if (exclude.includes(key)) continue;
      append(dl, element('dt', '', pretty(key)), element('dd', typeof value === 'object' ? 'code-value' : '', typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value ?? 'Not declared')));
    }
    return dl;
  }
  function renderDefinition(node, content) {
    const identity = section('Identity'); append(identity, fields({ id: node.id, kind: node.kind, parent: node.parent || 'Root membrane' })); content.appendChild(identity);
    const boundary = section('Boundary'); boundary.firstChild.appendChild(badge(node.boundary?.binding)); append(boundary, element('p', 'detail-copy', node.boundary?.description || 'Not declared'), fields(node.boundary, ['binding', 'description'])); content.appendChild(boundary);
    const physics = section('Physics'); physics.firstChild.appendChild(badge(node.physics?.status)); append(physics, element('p', 'detail-copy', node.physics?.description || 'Not declared'), fields(node.physics, ['status', 'description'])); content.appendChild(physics);
    const validation = section('Validation'); validation.firstChild.appendChild(badge(node.validation?.status)); const claims = element('div', 'validation-block'); claims.appendChild(fields(node.validation, ['status'])); validation.appendChild(claims); content.appendChild(validation);
  }
  function renderPorts(node, content) {
    if (node.kind === 'connection') { const endpoints = section('Connection endpoints'); endpoints.firstChild.appendChild(badge(node.connection_status)); append(endpoints, element('p', 'detail-copy', 'Navigate to either membrane to inspect its exposed interface.'), endpointPath(node)); content.appendChild(endpoints); }
    const ports = section('Exposed ports'); ports.firstChild.appendChild(element('span', 'source-count', String(list(node.ports).length)));
    if (!list(node.ports).length) ports.appendChild(empty('No ports declared on this membrane.'));
    list(node.ports).forEach(port => {
      const item = element('article', 'port-definition'); const title = element('h4', 'port-title'); append(title, element('span', 'port-dot'), element('span', '', port.id));
      const meta = element('div', 'port-meta'); append(meta, element('span', '', port.protocol), element('span', '', port.unit));
      append(item, title, meta, element('p', 'detail-copy', port.description));
      if (port.delegates_to) { const link = button('Exposes ' + nodeLabel(port.delegates_to.node) + '.' + port.delegates_to.port + ' ↗', 'inline-link', () => { navigate(port.delegates_to.node); setTab('ports'); }); const wrapper = element('div', 'port-links'); wrapper.appendChild(link); item.appendChild(wrapper); }
      const links = list(node.connections).map(id => state.nodes.get(id)).filter(connection => list(connection?.endpoints).some(endpoint => endpoint.node === node.id && endpoint.port === port.id));
      if (links.length) { const wrapper = element('div', 'port-links'); links.forEach(connection => wrapper.appendChild(button(connection.name + ' ↗', 'inline-link', () => { navigate(connection.id); setTab('ports'); }))); item.appendChild(wrapper); } else item.appendChild(element('p', 'source-note', 'Open port · no authored connection.'));
      ports.appendChild(item);
    }); content.appendChild(ports);
    const connected = section('Connection membranes'); connected.appendChild(list(node.connections).length ? connectionRows(node.connections) : empty('No connection membranes reference this membrane’s ports.')); content.appendChild(connected);
    content.appendChild(element('p', 'detail-copy', 'Protocol and unit compatibility is a structural check. It does not prove force transfer, stiffness, frame correctness or runtime readiness.'));
  }
  function renderSources(node, content) {
    const gaps = section('Declared gaps'); gaps.firstChild.appendChild(element('span', 'source-count', String(list(node.gaps).length)));
    if (list(node.gaps).length) { const entries = element('ul', 'gap-list'); node.gaps.forEach(gap => entries.appendChild(element('li', '', gap))); gaps.appendChild(entries); } else gaps.appendChild(empty('No gap text declared. This does not establish physical qualification.')); content.appendChild(gaps);
    const sources = section('Source files'); sources.appendChild(element('p', 'detail-copy', '“Present” means the file was inspected. Its hash identifies bytes, not proof.'));
    if (!list(node.sources).length) sources.appendChild(empty('No source references authored for this membrane.'));
    list(node.sources).forEach(path => {
      const source = state.sources.get(path); const status = source?.status || 'not inspected'; const entry = element('article', 'source-entry'); const head = element('div', 'source-header'); append(head, element('code', 'source-path', path), badge(status, status)); entry.appendChild(head);
      if (source?.raw_sha256) { const hash = element('p', 'source-hash', 'raw SHA-256 ' + source.raw_sha256); entry.appendChild(hash); }
      if (Number.isInteger(source?.bytes)) entry.appendChild(element('p', 'source-note', source.bytes.toLocaleString() + ' bytes inspected'));
      if (status !== 'present') entry.appendChild(element('p', 'source-note', 'Source bytes are unavailable in the inspected checkout. No substitute has been used.'));
      sources.appendChild(entry);
    }); content.appendChild(sources);
    const warnings = list(state.snapshot.warnings).filter(warning => warning.node === node.id || (!warning.node && node.id === state.snapshot.root));
    if (warnings.length) { const area = section('Snapshot warnings'); const entries = element('ul', 'gap-list'); warnings.forEach(warning => entries.appendChild(element('li', '', warning.code + ': ' + warning.detail))); area.appendChild(entries); content.appendChild(area); }
    const snapshot = section('Snapshot provenance'); snapshot.classList.add('snapshot-details'); snapshot.appendChild(fields({ authority: state.snapshot.authority, definition_raw_sha256: state.snapshot.definition_raw_sha256, snapshot_sha256: state.snapshot.snapshot_sha256 })); content.appendChild(snapshot);
    if (list(state.snapshot.limits).length) { const limits = section('Scope limits'); const entries = element('ul', 'limits-list'); state.snapshot.limits.forEach(limit => entries.appendChild(element('li', '', limit))); limits.appendChild(entries); content.appendChild(limits); }
  }
  function requirementList(values, className = 'requirements-list') {
    const entries = element('ul', className);
    list(values).forEach(value => entries.appendChild(element('li', '', typeof value === 'string' ? value : JSON.stringify(value))));
    return entries;
  }
  function revealWorkEntry(kind, id) {
    const target = Array.from($('detail-content').querySelectorAll('[data-work-id]')).find(item => item.dataset.workId === kind + ':' + id);
    if (target) { target.open = true; target.scrollIntoView({ block: 'nearest' }); const summary = target.querySelector('summary'); if (summary) summary.focus({ preventScroll: true }); }
  }
  function navigateTask(id) {
    const task = state.tasks.get(id); if (!task) return;
    state.focusedTask = id; state.focusedCheckpoint = null;
    if (state.nodes.has(task.ontology?.primary_membrane)) navigate(task.ontology.primary_membrane);
    setTab('work'); revealWorkEntry('task', id);
  }
  function navigateCheckpoint(id) {
    const checkpoint = state.checkpoints.get(id); if (!checkpoint) return;
    state.focusedCheckpoint = id; state.focusedTask = null;
    const target = list(checkpoint.membrane_ids).find(nodeId => state.nodes.has(nodeId) && list(state.nodes.get(nodeId).checkpoints).some(item => item.id === id));
    if (target) navigate(target);
    setTab('work'); revealWorkEntry('checkpoint', id);
  }
  function taskLink(id) {
    if (!state.tasks.has(id)) return element('code', 'reference-chip unavailable', id);
    const link = button(id, 'reference-chip', () => navigateTask(id)); link.title = state.tasks.get(id).title; link.setAttribute('aria-label', 'Open task ' + id + ': ' + state.tasks.get(id).title); return link;
  }
  function membraneLinks(ids) {
    const links = element('div', 'reference-links');
    list(ids).forEach(id => { if (state.nodes.has(id)) links.appendChild(button(nodeLabel(id) + ' ↗', 'reference-chip membrane-reference', () => { navigate(id); setTab('work'); })); else links.appendChild(element('code', 'reference-chip unavailable', id)); });
    return links;
  }
  function verificationProfile(profile) {
    const container = element('details', 'verification-profile');
    const summary = element('summary', '', 'Verification profile'); container.appendChild(summary);
    if (!profile || typeof profile !== 'object') { container.appendChild(empty('No verification profile attached to this snapshot.')); return container; }
    const body = element('div', 'verification-body');
    append(body, element('p', 'profile-id mono', profile.id || 'Profile ID not declared'), fields({ kind: profile.kind, subject: profile.subject, scenario: profile.scenario }));
    const diagnostics = element('section', 'profile-section'); append(diagnostics, element('h5', '', 'Diagnostic layers / 3D labels'), list(profile.diagnostic_layers).length ? requirementList(profile.diagnostic_layers) : element('p', 'source-note', 'No diagnostic layers listed in this profile.')); body.appendChild(diagnostics);
    const views = element('section', 'profile-section'); append(views, element('h5', '', 'Required views / angles'), list(profile.views).length ? requirementList(profile.views) : element('p', 'source-note', 'No visual views listed in this profile.')); body.appendChild(views);
    const clean = profile.clean_view_required === true ? 'Required · pair with the same state or reproducible command trace.' : profile.clean_view_required === false ? 'Not required by this profile.' : 'Not declared.';
    const cleanSection = element('section', 'profile-section'); append(cleanSection, element('h5', '', 'Clean view'), element('p', 'detail-copy', clean)); body.appendChild(cleanSection);
    const camera = element('section', 'profile-section'); append(camera, element('h5', '', 'Camera / distance receipt'));
    if (list(profile.camera_required_fields).length) {
      append(camera, element('p', 'source-note', 'Record actual numeric camera settings for each required view, including orientation and target distance. A view name alone is not enough.'), requirementList(profile.camera_required_fields, 'requirements-list camera-fields'));
      camera.appendChild(element('p', 'source-note', 'Derive framing from the subject bounds or reuse an approved bookmark. This profile supplies requirements, not an invented angle or distance.'));
    } else camera.appendChild(element('p', 'source-note', 'No camera fields listed in this profile.'));
    body.appendChild(camera);
    const falsifier = element('section', 'profile-section'); append(falsifier, element('h5', '', 'Falsifier'), element('p', 'detail-copy', typeof profile.falsifier === 'string' ? profile.falsifier : JSON.stringify(profile.falsifier ?? 'Not declared'))); body.appendChild(falsifier);
    body.appendChild(fields(profile, ['id', 'kind', 'subject', 'scenario', 'diagnostic_layers', 'views', 'clean_view_required', 'camera_required_fields', 'falsifier']));
    container.appendChild(body); return container;
  }
  function taskEntry(task, nodeId, initiallyOpen = false) {
    const entry = element('details', 'task-entry'); entry.dataset.workId = 'task:' + task.id; entry.open = state.focusedTask === task.id || initiallyOpen;
    const summary = element('summary', 'task-summary'); const top = element('span', 'task-line');
    append(top, element('code', 'task-id', task.id), element('span', 'task-relation', task.ontology?.primary_membrane === nodeId ? 'PRIMARY' : 'RELATED'));
    if (task.scope === 'conditional') top.appendChild(element('span', 'conditional-label', 'CONDITIONAL'));
    append(summary, top, element('span', 'task-title', task.title)); entry.appendChild(summary);
    const body = element('div', 'task-body');
    const layer = Number.isInteger(task.dependency_layer) ? 'Dependency layer ' + task.dependency_layer : 'Dependency layer not provided';
    append(body, element('p', 'dependency-label', layer + ' · logical order, not a time estimate'), element('p', 'task-scope', 'Scope: ' + pretty(task.scope)));
    if (task.scope === 'conditional') body.appendChild(element('p', 'conditional-note', 'Conditional work is not selected merely because this membrane is visible. Activation requires its existing gate.'));
    const dependencies = element('section', 'task-section'); dependencies.appendChild(element('h5', '', 'Required before this task'));
    if (list(task.depends_on).length) { const links = element('div', 'reference-links'); task.depends_on.forEach(id => links.appendChild(taskLink(id))); dependencies.appendChild(links); } else dependencies.appendChild(element('p', 'source-note', 'No explicit task dependencies.')); body.appendChild(dependencies);
    const acceptance = element('section', 'task-section'); append(acceptance, element('h5', '', 'Acceptance · done when'), element('p', 'task-acceptance', typeof task.done_when === 'string' ? task.done_when : JSON.stringify(task.done_when))); body.appendChild(acceptance);
    if (list(task.calculation_ids).length) { const calculations = element('section', 'task-section'); append(calculations, element('h5', '', 'Calculation contract IDs'), element('p', 'mono detail-copy', task.calculation_ids.join(', '))); body.appendChild(calculations); }
    if (task.ontology) {
      const mapping = element('section', 'task-section'); append(mapping, element('h5', '', 'Membrane / interface bindings'), membraneLinks([task.ontology.primary_membrane, ...list(task.ontology.related_membranes), ...list(task.ontology.connection_ids)].filter((id, index, all) => id && all.indexOf(id) === index))); body.appendChild(mapping);
      if (list(task.ontology.checkpoint_ids).length) { const checkpointArea = element('section', 'task-section'); checkpointArea.appendChild(element('h5', '', 'Integration checkpoints')); const links = element('div', 'reference-links'); task.ontology.checkpoint_ids.forEach(id => links.appendChild(state.checkpoints.has(id) ? button(id, 'reference-chip', () => navigateCheckpoint(id)) : element('code', 'reference-chip unavailable', id))); checkpointArea.appendChild(links); body.appendChild(checkpointArea); }
    }
    body.appendChild(verificationProfile(task.verification_profile)); entry.appendChild(body); return entry;
  }
  function checkpointEntry(checkpoint) {
    const entry = element('details', 'checkpoint-entry'); entry.dataset.workId = 'checkpoint:' + checkpoint.id; entry.open = state.focusedCheckpoint === checkpoint.id;
    const summary = element('summary', 'task-summary'); const top = element('span', 'task-line'); append(top, element('code', 'task-id', checkpoint.id), element('span', 'planned', 'PLANNED CHECKPOINT')); append(summary, top, element('span', 'task-title', checkpoint.name)); entry.appendChild(summary);
    const body = element('div', 'task-body');
    const tasks = element('section', 'task-section'); tasks.appendChild(element('h5', '', 'Required task IDs')); const links = element('div', 'reference-links'); list(checkpoint.task_ids).forEach(id => links.appendChild(taskLink(id))); tasks.appendChild(links); body.appendChild(tasks);
    if (list(checkpoint.requires).length) { const dependencies = element('section', 'task-section'); append(dependencies, element('h5', '', 'Prerequisite checkpoints')); const items = element('div', 'reference-links'); checkpoint.requires.forEach(id => items.appendChild(state.checkpoints.has(id) ? button(id, 'reference-chip', () => navigateCheckpoint(id)) : element('code', 'reference-chip unavailable', id))); dependencies.appendChild(items); body.appendChild(dependencies); }
    append(body, membraneLinks(checkpoint.membrane_ids));
    const acceptance = element('section', 'task-section'); append(acceptance, element('h5', '', 'Checkpoint acceptance'), element('p', 'task-acceptance', typeof checkpoint.acceptance === 'string' ? checkpoint.acceptance : JSON.stringify(checkpoint.acceptance))); body.appendChild(acceptance);
    body.appendChild(verificationProfile(checkpoint.verification_profile)); entry.appendChild(body); return entry;
  }
  function renderWork(node, content) {
    const plan = state.snapshot.plan;
    if (!plan) { append(content, empty('No work plan is attached to this snapshot. Refresh after the ontology API has the amended catalog.'), element('p', 'source-note', 'The membrane definition remains available. No tasks or acceptance results are synthesized.')); return; }
    const overview = section('Attached work plan');
    append(overview, element('p', 'plan-counts', plan.task_count + ' authored tasks · ' + plan.selected_count + ' selected'), element('p', 'plan-policy', plan.task_status_policy || 'Planned requirements; reconcile accepted evidence.'), element('p', 'source-note', 'Selection is scope, not completion. Dependency layers express logical readiness; independent membranes may progress in parallel.'));
    const hash = element('code', 'source-hash plan-hash', 'Scope SHA-256 ' + plan.scope_sha256); overview.appendChild(hash); content.appendChild(overview);
    const order = element('details', 'dependency-order'); const orderTitle = element('summary', '', 'Dependency order · ' + list(plan.dependency_layers).length + ' layers'); order.appendChild(orderTitle);
    const orderBody = element('div', 'dependency-order-body'); orderBody.appendChild(element('p', 'source-note', 'Layer numbers are not dates or durations. Existing receipts and ownership still govern dispatch.'));
    list(plan.dependency_layers).forEach((ids, index) => { const row = element('div', 'dependency-layer'); append(row, element('span', 'layer-number', 'Layer ' + index)); const links = element('div', 'reference-links'); list(ids).forEach(id => links.appendChild(taskLink(id))); row.appendChild(links); orderBody.appendChild(row); }); order.appendChild(orderBody); content.appendChild(order);
    const primary = list(node.tasks).filter(task => task.ontology?.primary_membrane === node.id), related = list(node.tasks).filter(task => task.ontology?.primary_membrane !== node.id);
    for (const [title, tasks, role] of [['Primary work', primary, 'primary'], ['Related / interface work', related, 'related']]) {
      const area = section(title); area.firstChild.appendChild(element('span', 'source-count', String(tasks.length)));
      if (!tasks.length) area.appendChild(empty(role === 'primary' ? 'No task in this snapshot names this membrane as its primary subject.' : 'No related task bindings declared for this membrane.'));
      [...tasks].sort((a, b) => (a.dependency_layer ?? Infinity) - (b.dependency_layer ?? Infinity) || a.id.localeCompare(b.id)).forEach((task, index) => area.appendChild(taskEntry(task, node.id, role === 'primary' && index === 0 && !state.focusedTask && !state.focusedCheckpoint))); content.appendChild(area);
    }
    const checkpoints = section('Integration checkpoints'); checkpoints.firstChild.appendChild(element('span', 'source-count', String(list(node.checkpoints).length)));
    if (!list(node.checkpoints).length) checkpoints.appendChild(empty('No integration checkpoint attached to this membrane.'));
    list(node.checkpoints).forEach(checkpoint => checkpoints.appendChild(checkpointEntry(checkpoint))); content.appendChild(checkpoints);
    content.appendChild(element('p', 'work-honesty', 'These are planned evidence requirements. A hierarchy, source hash or diagnostic label does not establish visual acceptance or a playable result.'));
  }
  function renderDetails() {
    const node = state.nodes.get(state.selected); if (!node) return;
    const content = $('detail-content'); content.replaceChildren();
    if (state.tab === 'ports') renderPorts(node, content); else if (state.tab === 'sources') renderSources(node, content); else if (state.tab === 'work') renderWork(node, content); else renderDefinition(node, content);
  }
  function renderError(error) {
    state.snapshot = null; state.bytes = null; state.nodes.clear(); state.sources.clear(); state.tasks.clear(); state.checkpoints.clear(); $('plan-summary').hidden = true;
    document.body.classList.add('error-state');
    $('tree').replaceChildren(element('p', 'loading-copy muted', 'Hierarchy unavailable. Refresh after the source error is resolved.'));
    $('detail-content').replaceChildren(empty('No snapshot available. Details are never synthesized.'));
    $('revision').textContent = 'Snapshot unavailable'; $('definition-hash').textContent = '—'; $('definition-hash').removeAttribute('title'); $('node-count').textContent = '—'; $('inspector-kind').textContent = '—'; $('structure-status').textContent = 'Read refused'; $('snapshot-hash').textContent = 'No snapshot loaded';
    const message = element('div', 'state-message'); const title = element('h2', '', 'Definition unavailable'); title.id = 'selected-title';
    append(message, title, element('p', '', 'The inspector could not load a valid snapshot. Check the local inspector server and resolve the refusal below, then refresh.'), element('div', 'error-code', error.message || 'Unknown read error'), button('Retry loading', 'button', load));
    $('main-content').replaceChildren(message); announce('Snapshot unavailable. ' + error.message);
  }
  async function load() {
    if (state.loading) return;
    state.loading = true; const previous = state.selected || hashNode();
    $('refresh').disabled = true; $('refresh').setAttribute('aria-busy', 'true'); $('download').disabled = true;
    announce('Reading the ontology snapshot.');
    const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch('/api/ontology', { cache: 'no-store', signal: controller.signal });
      const bytes = await response.arrayBuffer(); const text = new TextDecoder().decode(bytes); let snapshot;
      try { snapshot = JSON.parse(text); } catch { throw new Error('invalid_response: expected a JSON snapshot'); }
      if (!response.ok) throw new Error((snapshot.refused || 'read_failed') + ' · HTTP ' + response.status);
      if (snapshot.schema !== 'chimera.membrane_ontology.snapshot.v1' || !Array.isArray(snapshot.nodes) || !snapshot.nodes.some(node => node.id === snapshot.root) || snapshot.checks?.structural_valid !== true) throw new Error('invalid_snapshot: the API did not return a structurally valid ontology');
      state.snapshot = snapshot; state.bytes = bytes; state.nodes = new Map(snapshot.nodes.map(node => [node.id, node])); state.sources = new Map(list(snapshot.sources).map(source => [source.path, source]));
      state.tasks.clear(); state.checkpoints.clear();
      list(snapshot.plan?.checkpoints).forEach(checkpoint => state.checkpoints.set(checkpoint.id, checkpoint));
      snapshot.nodes.forEach(node => { list(node.tasks).forEach(task => state.tasks.set(task.id, task)); list(node.checkpoints).forEach(checkpoint => state.checkpoints.set(checkpoint.id, checkpoint)); });
      if (!state.expanded.size) { state.expanded.add(snapshot.root); list(state.nodes.get(snapshot.root).children).forEach(id => state.expanded.add(id)); }
      document.body.classList.remove('error-state');
      $('revision').textContent = 'Authored definition · revision ' + snapshot.revision; $('definition-hash').textContent = 'SHA ' + compactHash(snapshot.definition_raw_sha256); $('definition-hash').title = 'Definition raw SHA-256: ' + snapshot.definition_raw_sha256;
      $('node-count').textContent = snapshot.nodes.length; $('structure-status').textContent = 'Structure valid · ' + snapshot.checks.membranes + ' membranes · ' + snapshot.checks.ports + ' ports · ' + snapshot.checks.connections + ' connections';
      $('plan-summary').hidden = !snapshot.plan;
      if (snapshot.plan) { $('plan-summary').textContent = snapshot.plan.task_count + ' tasks · ' + snapshot.plan.selected_count + ' selected'; $('plan-summary').title = 'Authored scope, not completion. Scope SHA-256: ' + snapshot.plan.scope_sha256; }
      $('snapshot-hash').textContent = 'Snapshot ' + compactHash(snapshot.snapshot_sha256); $('snapshot-hash').title = snapshot.snapshot_sha256;
      navigate(previous || hashNode() || snapshot.root, false); announce('Snapshot loaded. ' + snapshot.nodes.length + ' membranes. ' + snapshot.checks.missing_sources + ' missing source files.');
    } catch (error) { renderError(error.name === 'AbortError' ? new Error('read_timeout: no snapshot received within 20 seconds') : error); }
    finally { clearTimeout(timeout); state.loading = false; $('refresh').disabled = false; $('refresh').removeAttribute('aria-busy'); ['download', 'search', 'expand-all', 'collapse-all'].forEach(id => { $(id).disabled = !state.snapshot; }); }
  }
  $('refresh').addEventListener('click', load);
  $('search').addEventListener('input', () => { state.search = $('search').value.trim().toLocaleLowerCase(); renderTree(); });
  $('expand-all').addEventListener('click', () => { state.nodes.forEach(node => state.expanded.add(node.id)); renderTree(); });
  $('collapse-all').addEventListener('click', () => { state.expanded.clear(); renderTree(); });
  $('download').addEventListener('click', () => { if (!state.bytes) return; const url = URL.createObjectURL(new Blob([state.bytes], { type: 'application/json' })); const link = element('a'); link.href = url; link.download = 'chimera-ontology-' + state.snapshot.snapshot_sha256.slice(0, 12) + '.json'; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); });
  document.querySelectorAll('[data-tab]').forEach(item => { item.addEventListener('click', () => setTab(item.dataset.tab)); item.addEventListener('keydown', event => { const tabs = ['definition', 'ports', 'sources', 'work']; let index = tabs.indexOf(state.tab); if (event.key === 'ArrowRight') index = (index + 1) % tabs.length; else if (event.key === 'ArrowLeft') index = (index + tabs.length - 1) % tabs.length; else if (event.key === 'Home') index = 0; else if (event.key === 'End') index = tabs.length - 1; else return; event.preventDefault(); setTab(tabs[index], true); }); });
  window.addEventListener('popstate', () => navigate(hashNode(), false));
  window.addEventListener('hashchange', () => navigate(hashNode(), false));
  load();
})();
