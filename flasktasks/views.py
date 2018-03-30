from flask import render_template, request, redirect, url_for, abort, jsonify
from collections import defaultdict
from flasktasks import app, db
from flasktasks.models import Mission, Task, Status, Tag, Color, LogEntry
from flasktasks.signals import task_created, mission_created 


@app.route('/')
def index():
	return render_template('home.html')
	
@app.route('/future')
def future():
	return render_template('future.html')

@app.route('/missions')
def missions():
	missions = Mission.query.all()
	return render_template('mission/index.html', missions=missions)

@app.route('/missions/new', methods=['POST', 'GET'])
def new_mission():
	if request.method == 'POST':
		mission = Mission(request.form.get('title'),
						  request.form.get('description'),
						  request.form.get('tag_id'))
		db.session.add(mission)
		db.session.commit()
		mission_created.send(mission)
		return redirect(url_for('missions'))
	else:
		tags = Tag.query.all()
		return render_template('mission/new.html', tags=tags)

@app.route('/tasks')
def tasks():
	mission = None
	if request.args.get('mission_id'):
		mission = Mission.query.get_or_404(request.args.get('mission_id'))
		tasks = Task.query.filter_by(mission_id=mission.id).all()
	else:
		return redirect(url_for('missions'))

	tasks_by_status = defaultdict(list)
	for task in tasks:
		status = Status(task.status).name 
		tasks_by_status[status].append(task)
	return render_template('task/index.html', tasks=tasks_by_status,
						   mission=mission)

@app.route('/tasks/new', methods=['POST', 'GET'])
def new_task():
	if request.method == 'POST':
		task = Task(request.form.get('title'),
					request.form.get('description'),
					request.form.get('mission_id'))
		db.session.add(task)
		db.session.commit()
		task_created.send(task)
		return redirect(url_for('tasks',mission_id=task.mission_id))
	else:
		missions = Mission.query.all()
		return render_template('task/new.html', missions=missions)

@app.route('/tasks/<int:task_id>')
def task(task_id):
	task = Task.query.get_or_404(task_id)
	return render_template('task/task.html', task=task)
	
@app.route('/tasks/<int:task_id>/edit', methods=['POST','GET'])
def edit_task(task_id):
	if request.method == 'POST':
		task = Task.query.get_or_404(task_id)
		task.title = request.form.get('title')
		task.description = request.form.get('description')
		db.session.commit()
		return redirect(url_for('tasks',mission_id=task.mission_id))
	else:
		task = Task.query.get_or_404(task_id)
		return render_template('task/edit.html', task=task)

@app.route('/tasks/<int:task_id>/set_status/<status>')
def set_status(task_id, status):
	task = Task.query.get_or_404(task_id)
	try:
		task.status = Status[status.upper()].value
	except KeyError:
		abort(400)

	db.session.add(task)
	db.session.commit()
	return redirect(url_for('tasks'))
	
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
	task = Task.query.get_or_404(task_id)
	mission = task.mission_id
	db.session.delete(task)
	db.session.commit()
	return url_for('tasks',mission_id=mission)
	
@app.route('/missions/<int:mission_id>', methods=['DELETE'])
def delete_mission(mission_id):
	mission = Mission.query.get_or_404(mission_id)
	db.session.delete(mission)
	db.session.commit()
	return url_for('missions')

@app.route('/tags/new', methods=['POST', 'GET'])
def new_tag():
	if request.method == 'POST':
		try:
			color = Color(int(request.form.get('color_id')))
		except ValueError:
			abort(400)
		tag = Tag(request.form.get('name'), color)
		db.session.add(tag)
		db.session.commit()
		return redirect(url_for('missions'))
	else:
		colors = { color.name: color.value for color in Color }
		return render_template('tags/new.html', colors=colors)


@app.route('/log')
def log():
	log_entries = LogEntry.query.all()
	return render_template('log.html', log_entries=log_entries)
