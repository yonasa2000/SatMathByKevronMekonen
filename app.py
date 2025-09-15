from flask import Flask, render_template, url_for, request, session, redirect, url_for
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure random value

try:
	with open('Static/March2025_Q&A/Algebra/linear_equations_one_variable.json', 'r', encoding='utf-8') as f:
		linear_eq_questions = json.load(f)
	with open('Static/March2025_Q&A/Algebra/linear_functions.json', 'r', encoding='utf-8') as f:
		linear_functions_questions = json.load(f)
	with open('Static/March2025_Q&A/Algebra/linear_equations_two_variable.json', 'r', encoding='utf-8') as f:
		linear_eq_two_questions = json.load(f)
	with open('Static/March2025_Q&A/Algebra/Systems_Two_Linear_Equations_Two_Variables.json', 'r', encoding='utf-8') as f:
		system_linear_eq_questions = json.load(f)
	with open('Static/March2025_Q&A/Algebra/Linear_InequalitiesIn_One_Two_Variables.json', 'r', encoding='utf-8') as f:
		linear_ineq_questions = json.load(f)
	with open('Static/March2025_Q&A/AdvancedMath/equivalent_expressions.json', 'r', encoding='utf-8') as f:
		equivalent_expressions = json.load(f)
	with open('Static/March2025_Q&A/AdvancedMath/nonlinear_equations_systems.json', 'r', encoding='utf-8') as f:
		nonlinear_equations_systems = json.load(f)
	with open('Static/March2025_Q&A/AdvancedMath/nonlinear_functions.json', 'r', encoding='utf-8') as f:
		nonlinear_functions = json.load(f)
except FileNotFoundError:
    linear_eq_questions = []
	
questions = {
    'linear-equations-one-variable': linear_eq_questions,
    'linear-functions': linear_functions_questions,
    'linear-equations-two-variables': linear_eq_two_questions,
    'systems-two-linear-equations-two-variables': system_linear_eq_questions,
    'linear-inequalities': linear_ineq_questions,
    'equivalent-expressions': equivalent_expressions,
    'nonlinear-equations-systems': nonlinear_equations_systems,
    'nonlinear-functions': nonlinear_functions,
    'ratio-rates-proportional-units': [],
    'percentages': [],
    'one-variable-data-distributions-center-spread': [],
    'two-variable-data-models-scatterplots': [],
    'probability-conditional-probability': [],
    'inference-sample-statistics-margin-error': [],
    'evaluating-statistical-claims-studies-experiments': [],
    'area-volume': [],
    'lines-angles-triangles': [],
    'right-triangles-trigonometry': [],
    'circles': []
}

@app.route('/category/<main_slug>/<mini_slug>', methods=['GET', 'POST'])
def mini_category(main_slug, mini_slug):
	main_cat = next((c for c in categories if c['slug'] == main_slug), None)
	mini_cat = None
	if main_cat:
		mini_cat = next((m for m in main_cat.get('mini_categories', []) if m['slug'] == mini_slug), None)
	# Get selected difficulties from query or form
	if request.method == 'POST':
		selected_difficulties = request.form.getlist('difficulty')
		marked_filter = request.form.get('marked_filter', request.args.get('marked_filter', 'all'))
	else:
		selected_difficulties = request.args.getlist('difficulty')
		marked_filter = request.args.get('marked_filter', 'all')
	print('Selected difficulties:', selected_difficulties)
	# Get all questions for this mini-category
	mini_cat_questions = questions.get(mini_slug, [])
	# Only re-filter on GET requests (initial load or filter change)
	if request.method == 'GET':
		if selected_difficulties:
			qs = [q for q in mini_cat_questions if q.get('difficulty') in selected_difficulties]
		else:
			qs = mini_cat_questions
		if marked_filter == 'yes':
			qs = [q for q in qs if q.get('marked', False)]
		elif marked_filter == 'no':
			qs = [q for q in qs if not q.get('marked', False)]
		session[f'filtered_qs_{mini_slug}'] = [q.get('id') for q in qs]
	else:
		# On POST, use the last filtered set from session
		qs_ids = session.get(f'filtered_qs_{mini_slug}', [])
		qs = [q for q in mini_cat_questions if q.get('id') in qs_ids]
	print('Filtered questions:', qs)

	progress_key = f'progress_{mini_slug}'
	answers_key = f'answers_{mini_slug}'
	feedback_key = f'feedback_{mini_slug}'
	last_attempt_key = f'last_attempt_{mini_slug}'
	marked_key = f'marked_{mini_slug}'

	# Always use the full mini-category question list for session arrays
	all_questions = questions.get(mini_slug, [])
	if request.method == 'GET':
		reset_needed = (
			progress_key not in session or
			answers_key not in session or len(session[answers_key]) != len(all_questions) or
			feedback_key not in session or len(session[feedback_key]) != len(all_questions) or
			marked_key not in session or len(session[marked_key]) != len(all_questions)
		)
		if reset_needed:
			session[progress_key] = 0
			session[answers_key] = [None] * len(all_questions)
			session[feedback_key] = [None] * len(all_questions)
			session[marked_key] = [q.get('marked', False) for q in all_questions]
		# Only sync session marked status to global questions data for all questions in mini-category on GET
		marked_session = session.get(marked_key, [q.get('marked', False) for q in all_questions])
		for idx, real_q in enumerate(all_questions):
			if idx < len(marked_session):
				real_q['marked'] = marked_session[idx]
	# For filtered questions, use the correct indices from the full session arrays
	# Map filtered qs to their index in all_questions for marking, answers, etc.

	current_index = session.get(progress_key, 0)
	# Reset index if out of bounds for filtered questions
	if current_index >= len(qs):
		current_index = 0
		session[progress_key] = 0
	current_question = qs[current_index] if current_index < len(qs) else None
	answers = session.get(answers_key, [None] * len(qs))
	feedback = session.get(feedback_key, [None] * len(qs))
	last_attempt = session.get(last_attempt_key)
	# Map marked status for filtered questions from the full session marked array
	full_marked = session.get(marked_key, [q.get('marked', False) for q in all_questions])
	marked = []
	for q in qs:
		idx = next((i for i, real_q in enumerate(all_questions) if real_q.get('id') == q.get('id')), None)
		marked.append(full_marked[idx] if idx is not None else False)

	show_feedback = None

	if request.method == 'POST':
		action = request.form.get('action')
		answer = request.form.get('answer')
		# Preserve difficulty filter in redirect
		difficulties = request.form.getlist('difficulty')
		marked_filter_val = request.form.get('marked_filter', marked_filter)
		difficulty_query = '&'.join([f'difficulty={d}' for d in difficulties])
		if marked_filter_val:
			difficulty_query += f'&marked_filter={marked_filter_val}'
		if action == 'submit':
			# Save answer and feedback
			if answer is not None and answer != '':
				answers[current_index] = answer
				correct = (answer == current_question.get('answer'))
				feedback[current_index] = 'Correct!' if correct else f'Incorrect. Correct answer: {current_question.get("answer")}'
				session[answers_key] = answers
				session[feedback_key] = feedback
				show_feedback = feedback[current_index]
		elif action == 'next':
			# Move to next question without submitting
			if current_index < len(qs) - 1:
				session[progress_key] = current_index + 1
			else:
				session[progress_key] = current_index
		elif action == 'prev':
			if current_index > 0:
				session[progress_key] = current_index - 1
		elif action == 'toggle_marked':
			# Find the index of the current question in the full mini-category question list
			all_questions = questions.get(mini_slug, [])
			filtered_q = qs[current_index]
			real_index = next((i for i, q in enumerate(all_questions) if q.get('id') == filtered_q.get('id')), None)
			if real_index is not None:
				marked_session = session.get(marked_key, [q.get('marked', False) for q in all_questions])
				# Toggle only the intended question
				marked_session[real_index] = not marked_session[real_index]
				session[marked_key] = marked_session
				all_questions[real_index]['marked'] = marked_session[real_index]
		# After marking/unmarking, do NOT re-filter; just reload the same filtered set
		return redirect(url_for('mini_category', main_slug=main_slug, mini_slug=mini_slug) + ('?' + difficulty_query if difficulty_query else ''))

	finished = current_index >= len(qs)
	if current_index < len(feedback):
		show_feedback = feedback[current_index]

	return render_template(
		'mini_category.html',
		main_category=main_cat,
		mini_category=mini_cat,
		question=current_question,
		finished=finished,
		answers=answers,
		total=len(qs),
		current_index=current_index,
		show_feedback=show_feedback,
		last_attempt=last_attempt,
		marked=marked
	)





# SAT Math main categories with mini-categories
categories = [
	{
		'name': 'Algebra',
		'slug': 'algebra',
		'mini_categories': [
			{'name': 'Linear Equations in One Variable', 'slug': 'linear-equations-one-variable'},
			{'name': 'Linear Functions', 'slug': 'linear-functions'},
			{'name': 'Linear Equations in Two Variables', 'slug': 'linear-equations-two-variables'},
			{'name': 'Systems of Two Linear Equations in Two Variables', 'slug': 'systems-two-linear-equations-two-variables'},
			{'name': 'Linear Inequalities', 'slug': 'linear-inequalities'}
		]
	},
	{
		'name': 'Advanced Math',
		'slug': 'advanced-math',
		'mini_categories': [
			{'name': 'Equivalent Expressions', 'slug': 'equivalent-expressions'},
			{'name': 'Nonlinear Equations in One Variable and Systems of Equations in Two Variables', 'slug': 'nonlinear-equations-systems'},
			{'name': 'Nonlinear Functions', 'slug': 'nonlinear-functions'}
		]
	},
	{
		'name': 'Problem-Solving and Data Analysis',
		'slug': 'problem-solving-data-analysis',
		'mini_categories': [
			{'name': 'Ratio, Rates, Proportional Relationships, and Units', 'slug': 'ratio-rates-proportional-units'},
			{'name': 'Percentages', 'slug': 'percentages'},
			{'name': 'One-Variable Data: Distributions and Measures of Center and Spread', 'slug': 'one-variable-data-distributions-center-spread'},
			{'name': 'Two-Variable Data: Models and Scatterplots', 'slug': 'two-variable-data-models-scatterplots'},
			{'name': 'Probability and Conditional Probability', 'slug': 'probability-conditional-probability'},
			{'name': 'Inference from Sample Statistics and Margin of Error', 'slug': 'inference-sample-statistics-margin-error'},
			{'name': 'Evaluating Statistical Claims: Observational Studies and Experiments', 'slug': 'evaluating-statistical-claims-studies-experiments'}
		]
	},
	{
		'name': 'Geometry and Trigonometry',
		'slug': 'geometry-trigonometry',
		'mini_categories': [
			{'name': 'Area and Volume', 'slug': 'area-volume'},
			{'name': 'Lines, Angles, and Triangles', 'slug': 'lines-angles-triangles'},
			{'name': 'Right Triangles and Trigonometry', 'slug': 'right-triangles-trigonometry'},
			{'name': 'Circles', 'slug': 'circles'}
		]
	}
]



@app.route('/')
def home():
	# Get selected difficulties from form or query
	selected_difficulties = request.args.getlist('difficulty')
	if not selected_difficulties:
		selected_difficulties = ['easy', 'medium', 'hard']
	marked_filter = request.args.get('marked_filter', 'all')
	bluebook_filter = request.args.get('bluebook_filter', 'both')
	# Remove release_date_filter
	# release_date_filter = request.args.get('release_date_filter', 'all')

	# Add question counts to each mini-category based on filter
	categories_with_counts = []
	for cat in categories:
		mini_with_counts = []
		for mini in cat['mini_categories']:
			filtered_questions = [q for q in questions.get(mini['slug'], []) if q.get('difficulty') in selected_difficulties]
			if marked_filter == 'yes':
				filtered_questions = [q for q in filtered_questions if q.get('marked', False)]
			elif marked_filter == 'no':
				filtered_questions = [q for q in filtered_questions if not q.get('marked', False)]
			# Bluebook filter
			if bluebook_filter == 'yes':
				filtered_questions = [q for q in filtered_questions if q.get('active', '') == 'yes']
			elif bluebook_filter == 'no':
				filtered_questions = [q for q in filtered_questions if q.get('active', '') != 'yes']
			# Remove release_date filter
			# if release_date_filter != 'all':
			#     filtered_questions = [q for q in filtered_questions if q.get('release_date', '') == release_date_filter]
			count = len(filtered_questions)
			mini_with_counts.append({**mini, 'count': count})
		categories_with_counts.append({**cat, 'mini_categories': mini_with_counts})
	return render_template('index.html', categories=categories_with_counts, selected_difficulties=selected_difficulties, marked_filter=marked_filter, bluebook_filter=bluebook_filter)

@app.route('/category/<slug>')
def category(slug):
	qs = questions.get(slug, [])
	cat = next((c for c in categories if c['slug'] == slug), None)
	return render_template('category.html', category=cat, questions=qs)

if __name__ == '__main__':
	app.run(debug=True)
