using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class movement01 : MonoBehaviour {

	[SerializeField]
	float speed = 5;

	// Use this for initialization
	void Start () {
		
	}
	
	// Update is called once per frame
	void Update () {

		float horMov = Input.GetAxis("Horizontal");
		float verMov = Input.GetAxis("Vertical");

		Vector3 direction = new Vector3 (0, 0, 0);

		direction.z = horMov;
		direction.y = verMov;

		transform.Translate (direction * (speed * Time.deltaTime));

	}
}
