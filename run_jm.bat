mkdir jmeter\results\llama3.2-3b\160_320

jmeter -n -t jmeter\test_plans\ticket-load-test3B.jmx ^
  -l jmeter\results\llama3.2-3b\160_320\run1.jtl ^
  -j jmeter\results\llama3.2-3b\160_320\run1.jmeter.log ^
  -Jsample_variables=row,request_id ^
  -Jhost=localhost -Jport=8000 ^
  -Jpost_rate=160 -Jsearch_rate=320