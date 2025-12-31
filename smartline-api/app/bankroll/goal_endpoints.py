"""
Goal Tracking Endpoints - Phase 3
==================================
CRUD operations for profit goals
"""

# Add these to your bankroll_endpoints.py

"""
@router.post("/goals")
async def create_goal(
    goal_type: str,
    goal_amount: Decimal,
    start_date: str,
    end_date: str,
    description: str = None,
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    '''
    Create a new profit goal.
    
    **Use Case:** Goal creation from dashboard
    **Returns:** Created goal with ID
    '''
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO user_goals (
                user_id, goal_type, goal_amount, 
                start_date, end_date, description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        ''', [user_id, goal_type, goal_amount, start_date, end_date, description])
        
        goal = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        return goal
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")

@router.get("/goals")
async def get_goals(
    user_id: int = Query(default=1),
    status: str = Query(default='active'),
    conn = Depends(get_db)
):
    '''
    Get user goals with progress.
    
    **Use Case:** Goals dashboard
    **Returns:** List of goals with progress
    '''
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM v_goal_progress
            WHERE user_id = %s
            AND (%s = 'all' OR status = %s)
            ORDER BY end_date DESC
        ''', [user_id, status, status])
        
        goals = cursor.fetchall()
        cursor.close()
        
        return goals
        
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get goals: {str(e)}")

@router.put("/goals/{goal_id}")
async def update_goal(
    goal_id: int,
    goal_amount: Decimal = None,
    end_date: str = None,
    description: str = None,
    status: str = None,
    conn = Depends(get_db)
):
    '''
    Update a goal.
    
    **Use Case:** Edit goal from dashboard
    **Returns:** Updated goal
    '''
    cursor = conn.cursor()
    
    try:
        update_fields = []
        params = []
        
        if goal_amount is not None:
            update_fields.append("goal_amount = %s")
            params.append(goal_amount)
        if end_date is not None:
            update_fields.append("end_date = %s")
            params.append(end_date)
        if description is not None:
            update_fields.append("description = %s")
            params.append(description)
        if status is not None:
            update_fields.append("status = %s")
            params.append(status)
            if status == 'completed':
                update_fields.append("completed_at = NOW()")
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(goal_id)
        query = f'''
            UPDATE user_goals
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE goal_id = %s
            RETURNING *
        '''
        
        cursor.execute(query, params)
        goal = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return goal
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to update goal: {str(e)}")

@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: int,
    conn = Depends(get_db)
):
    '''
    Delete a goal.
    
    **Use Case:** Remove goal from dashboard
    **Returns:** Success message
    '''
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM user_goals WHERE goal_id = %s RETURNING goal_id", [goal_id])
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return {"success": True, "message": "Goal deleted"}
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete goal: {str(e)}")
"""
