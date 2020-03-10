using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class test01 : MonoBehaviour 
{
	[SerializeField]
	GameObject cubePrefab;

	// Use this for initialization
	void Start() 
	{
		//cubePrefab = GameObject.Find("Culo");
		Debug.Log("Cane cane = Spawned by: " + gameObject.name, gameObject);	
		Instantiate( cubePrefab );
	}
	
	// Update is called once per frame
	void Update() 
	{
		if (Input.GetMouseButtonUp(0)) {
			Instantiate( cubePrefab, 
				         new Vector3( Random.Range(-5, 5),
				                       Random.Range(-5, 5),
				                       Random.Range(-5, 5)),
				         cubePrefab.transform.rotation
			 	);
		}
	}
}
