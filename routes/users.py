
from flask import Blueprint, request,jsonify 
from db import db
from pymongo import ReturnDocument
from datetime import datetime, timezone,timedelta
from bson import ObjectId
from utils.error_log import log_error_to_db
import traceback,os,inspect
from routes.trainings_routes import trainings_bp
from email_services.email_utils import send_training_email



def format_date(date_val):
    if not date_val:
        return None
    try:
        if isinstance(date_val, str):
            dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
        else:
            dt = date_val
        return dt.strftime('%b %d, %Y')
    except Exception:
        return str(date_val)

def format_training_dates(assigned_date, start_date, time_period):
   
    from datetime import timedelta
    assigned_date_fmt = format_date(assigned_date) or "not assigned"
    if start_date is None:
        start_date_fmt = "Not started"
        due_date_fmt = "Not started"
    else:
        start_date_dt = None
        try:
            if isinstance(start_date, str):
                start_date_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                start_date_dt = start_date
            start_date_fmt = start_date_dt.strftime('%b %d, %Y')
            if time_period is not None:
                due_date_dt = start_date_dt + timedelta(days=int(time_period))
                due_date_fmt = due_date_dt.strftime('%b %d, %Y')
            else:
                due_date_fmt = "unknown"
        except Exception:
            start_date_fmt = str(start_date)
            due_date_fmt = "unknown"
    return assigned_date_fmt, start_date_fmt, due_date_fmt


users_bp=Blueprint('users', __name__)
file_path = os.path.relpath(inspect.getfile(inspect.currentframe()))



@users_bp.route('/user-dashboard')
def get_user_dashboard_data():
    try:
        data=request.get_json()
        emp_id=data.get('emp_id')
        
        trainings=list(db['trainings'].find())
        
        assigned=0
        completed=0
        due=0
        emp_trainings={}
        for training in trainings:
            
            for a in training.get('assigned_to',[]):
                if a.get['emp_id'] == emp_id:
                    emp_trainings.append({
                        'title':trainings.get('title'),
                        'time_period':trainings.get('time_period'),
                        'status':a.get('status'),
                        'progress':a.get('progress')
                    })
                    
                    assigned=assigned + 1
                    if a.get('status')=='completed' :
                        completed=completed+1
                    elif a.get('status')=='due':
                        due=due+1
                        
        return jsonify(emp_trainings)
                    
        
    except Exception as e:
        log_error_to_db(
            level="error",
            message=str(e),
            stack_trace=traceback.format_exc(),
            time=datetime.now(timezone.utc),
            path=file_path,
            method="get_user_dashboard_data",
            ip=request.remote_addr
        )
        return jsonify({"error": str(e)}), 500



# To know how many trainings are assigned to user with id
@users_bp.route('/users-trainings', methods=['POST'])
def get_trainings_for_single_user():
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        all_trainings = list(db['trainings'].find())

        employee_trainings = []

        for training in all_trainings:
            assigned_to = training.get('assigned_to', [])
            for idx, a in enumerate(assigned_to):
                if a.get('emp_id') == emp_id:
                    start_date = a.get('start_date')
                    time_period = training.get('time_period', 0) or 0

                    # Parse start_date
                    if isinstance(start_date, str):
                        try:
                            start_date_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        except Exception:
                            start_date_dt = None
                    else:
                        start_date_dt = start_date

                    # Calculate due date
                    due_date_calc = None
                    if start_date_dt:
                        due_date_calc = start_date_dt + timedelta(days=int(time_period))

                    stored_due_date = a.get('due_date')
                    if isinstance(stored_due_date, str):
                        try:
                            stored_due_date_dt = datetime.fromisoformat(stored_due_date.replace('Z', '+00:00'))
                        except Exception:
                            stored_due_date_dt = None
                    else:
                        stored_due_date_dt = stored_due_date

                    # Update due_date in DB if needed
                    if due_date_calc and (not stored_due_date_dt or due_date_calc.date() != stored_due_date_dt.date()):
                        db['trainings'].update_one(
                            {'_id': training['_id'], f'assigned_to.{idx}.emp_id': emp_id},
                            {'$set': {f'assigned_to.{idx}.due_date': due_date_calc}}
                        )
                        due_date_to_use = due_date_calc
                    else:
                        due_date_to_use = stored_due_date if stored_due_date else due_date_calc

                    employee_trainings.append({
                        "id": str(training.get('_id')),
                        "title": training.get('title'),
                        "assigned_date": a.get('assigned_date'),
                        "status": a.get('status'),
                        "progress": a.get("progress"),
                        "start_date": a.get('start_date'),
                        "due_date": due_date_to_use
                    })

        return jsonify({
            "message": f"Trainings assigned to user {emp_id}",
            "data": employee_trainings
        }), 200

    except Exception as e:
        log_error_to_db(
            level="error",
            message=str(e),
            stack_trace=traceback.format_exc(),
            time=datetime.now(timezone.utc),
            path=file_path,
            method="get_trainings_for_single_user",
            ip=request.remote_addr
        )
        return jsonify({'error': str(e)}), 500


    except Exception as e:
        log_error_to_db(
            level="error",
            message=str(e),
            stack_trace=traceback.format_exc(),
            time=datetime.now(timezone.utc),
            path=file_path,
            method="get_trainings_for_single_user",
            ip=request.remote_addr
        )
        return jsonify({'error': str(e)}), 500


@users_bp.route('/user-dashboard',methods=["POST"])
def user_dashboard_data():
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        if not emp_id:
            return jsonify({"error": "emp_id is required"}), 400

        all_trainings = list(db['trainings'].find())

        assigned = 0
        completed = 0
        due = 0
        employee_trainings = []

        for training in all_trainings:
            training_status = training.get('trainings_status', '')  
           
            assigned_to = training.get('assigned_to', [])
            for idx, a in enumerate(assigned_to):
                if a.get('emp_id') == emp_id:
                    assigned += 1
                    completed += 1 if a.get('status') == 'completed' else 0
                    due += 1 if str(a.get("status", "")).strip().lower() in ["due", "assigned"] else 0

                    start_date = a.get('start_date')
                    time_period = training.get('time_period', 0) or 0

                    if isinstance(start_date, str):
                        try:
                            start_date_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        except Exception:
                            start_date_dt = None
                    else:
                        start_date_dt = start_date

                    due_date_calc = None
                    if start_date_dt:
                        due_date_calc = start_date_dt + timedelta(days=int(time_period))

                    stored_due_date = a.get('due_date')
                    if isinstance(stored_due_date, str):
                        try:
                            stored_due_date_dt = datetime.fromisoformat(stored_due_date.replace('Z', '+00:00'))
                        except Exception:
                            stored_due_date_dt = None
                    else:
                        stored_due_date_dt = stored_due_date

                    if due_date_calc and (not stored_due_date_dt or due_date_calc.date() != stored_due_date_dt.date()):
                        db['trainings'].update_one(
                                {'_id': training['_id'], f'assigned_to.{idx}.emp_id': emp_id},
                                {'$set': {f'assigned_to.{idx}.due_date': due_date_calc}}
                            )
                        due_date_to_use = due_date_calc
                    else:
                        due_date_to_use = stored_due_date if stored_due_date else due_date_calc

                    employee_trainings.append({
                        "title": training.get('title'),
                        "assigned_department": a.get('assigned_department') if a.get('assigned_department') else "Full Stack Developer",
                        "id": str(training.get('_id')),
                        "assigned_date": a.get('assigned_date'),
                        "status": a.get('status'),
                        "progress": a.get("progress"),
                        "start_date": a.get('start_date'),
                        "due_date": due_date_to_use,
                        "last_accessed": a.get('last_accessed'),
                        "trainings_status":training.get("trainings_status")
                    })
                    
        return jsonify({
            'cardStats': {
                'completed': completed,
                'assigned': assigned,
                'due': due
            },
            'trainings': employee_trainings,
            "message": f"Trainings assigned to user {emp_id}"
        }), 200

    except Exception as e:
        log_error_to_db(
            level="error",
            message=str(e),
            stack_trace=traceback.format_exc(),
            time=datetime.now(timezone.utc),
            path=file_path,
            method="user_dashboard_data",
            ip=request.remote_addr
        )
        return jsonify({'error': str(e)}), 500

    
@users_bp.route('/assign-trainings', methods=["POST"])
def assign_trainings():
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        name=data.get('name')
        email=data.get('email')
        department=data.get('department')
        assigned_trainings = data.get('assignedTrainings', [])
        updated_trainings = []

        for training in assigned_trainings:
            training_id = training.get('id')
            t = db['trainings'].find_one({'_id': ObjectId(training_id)})
            for emp in t.get('assigned_to',[]):
                if emp_id == emp.get('emp_id'):
                    return jsonify({
                        'error': f"Training {t.get('title')} is already assigned to user {emp_id}."
                    }), 400
            enrolled_employees=t.get('enrolled_employees')+1
            due_employees=t.get('due')+1

            due_date = t.get('due')
            training_title = t.get('title')

            if not t:
                continue
            start_date = datetime.now(timezone.utc)
            time_period = t.get('time_period', 0) or 0
            due_date = start_date + timedelta(days=int(time_period))
            assignment = {
                "emp_id": emp_id,
                "name":name,
                'email':email,
                "status": "assigned",
                "start_date": start_date,
                "due_date": due_date,
                "assigned_date": start_date,
                'assigned_department': department,
                "progress": 0,
                "last_accessed": None
            }
            db['trainings'].update_one(
                {'_id': ObjectId(training_id)},
                {'$push': {'assigned_to': assignment},
                 '$set': {'enrolled_employees': enrolled_employees,'due':due_employees} }
            )
            updated_trainings.append({
                'training_id': training_id,
                'training_title': training.get('title'),
                'assignment': assignment
            })
            send_training_email(
                to=email,
                name=name,
                title=training_title,
                due_date=due_date.strftime("%Y-%m-%d") if due_date else "N/A",
                subject="New Training Assigned",
                heading="Training Assigned",
                type="assign"
            )

        return jsonify({
            'message': f"{len(updated_trainings)} trainings assigned to user {emp_id}",
            'assigned_trainings': updated_trainings
        }), 200

    except Exception as e:
        print(e)
        log_error_to_db(
            level="error",
            message=str(e),
            stack_trace=traceback.format_exc(),
            time=datetime.now(timezone.utc),
            path=file_path,
            method="users_trainings",
            ip=request.remote_addr
        )
        return jsonify({'error': str(e)}), 500



@users_bp.route('/update-training-status',methods=['POST'])
def update_training_status():
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        training_id = data.get('training_id')
        status = data.get('status')
        progress = data.get('progress', 0)
        last_content_slide = data.get('lastContentSlide') 
        # print(training_id, emp_id, status, progress)
        
    
        
        if not emp_id or not training_id or not status:
            return jsonify({"error": "emp_id, training_id and status are required"}), 400
        
        training = db['trainings'].find_one({'_id': ObjectId(training_id)})
        if not training:
            return jsonify({"error": "Training not found"}), 404
        
        assigned_to = training.get('assigned_to', [])
        found = False
        for idx, a in enumerate(assigned_to):
            if a.get('emp_id') == emp_id:
                found = True
                update_fields = {
                    f'assigned_to.{idx}.status': status,
                    f'assigned_to.{idx}.progress': progress,
                    f'assigned_to.{idx}.last_accessed': datetime.now(timezone.utc)
                }
                if last_content_slide is not None:
                    update_fields[f'assigned_to.{idx}.lastContentSlide'] = last_content_slide 
                    
                inc_fields = {}
                if status == 'completed':
                    update_fields[f'assigned_to.{idx}.completed_date'] = datetime.now(timezone.utc)
                    inc_fields = {'due': -1, 'completed': 1}
                    
                db['trainings'].update_one(
                    {'_id': ObjectId(training_id)},
                    {'$set': update_fields, '$inc': inc_fields} if inc_fields else {'$set': update_fields}
                )
                break
        if not found:
            return jsonify({"error": "Assignment for this user not found in training."}), 404
        return jsonify({"message": "Training status updated successfully."}), 200
    except Exception as e:
        print(e)
        log_error_to_db(
            level="error",
            message=str(e),
            stack_trace=traceback.format_exc(),
            time=datetime.now(timezone.utc),
            path=file_path,
            method="update_training_status",
            ip=request.remote_addr
        )
        return jsonify({"error": str(e)}), 500
    
@users_bp.route('/delete-training', methods=['DELETE'])
def delete_training():
    try:
        data = request.get_json()
        training_id = data.get('training_id')
        emp_id = data.get('emp_id')
        
        if not training_id or not emp_id:
            return jsonify({"error": "training_id and emp_id are required"}), 400
        
        training = db['trainings'].find_one({'_id': ObjectId(training_id)})

        if not training:
            return jsonify({"error": "Training not found"}), 404

        # Find the assigned employee object
        assigned_to = training.get('assigned_to', [])
        employee = next((e for e in assigned_to if e.get('emp_id') == emp_id), None)

        if not employee:
            return jsonify({"error": "Employee not assigned to this training"}), 404

        # Prepare decrement values
        update_fields = {
            '$pull': {'assigned_to': {'emp_id': emp_id}},
            '$inc': {'enrolled_employees': -1}
        }

        if employee.get('status') == 'completed':
            update_fields['$inc']['completed'] = -1
        elif employee.get('status') == 'assigned' and employee.get('due', 0) > 0:
            update_fields['$inc']['due'] = -1

        # Perform update
        db['trainings'].update_one({'_id': ObjectId(training_id)}, update_fields)

        return jsonify({"success": True, "message": "Training assignment removed successfully"}), 200

    
    except Exception as e:
        log_error_to_db(
            level="error",
            message=str(e),
            stack_trace=traceback.format_exc(),
            time=datetime.now(timezone.utc),
            path=file_path,
            method="delete_training",
            ip=request.remote_addr
        )
        return jsonify({"error": str(e)}), 500  