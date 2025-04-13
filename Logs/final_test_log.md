# Project Test Log

## Client API Testing
- **POST /kv (5000, ui:test)**: Success, {"key":"ui","status":"success","value":"test"}
- **GET /kv/ui (5000)**: Success, {"key":"ui","value":"test"}
- **PUT /kv (5000, ui:updated)**: Success, {"key":"ui","status":"success","value":"updated"}
- **DELETE /kv/ui (5000)**: Success, {"key":"ui","status":"success"}
- **POST /kv (5001, ui2:test2)**: Success, {"key":"ui2","status":"success","value":"test2"}
- **GET /kv/ui2 (5001)**: Success, {"key":"ui2","value":"test2"}
- **GET /kv/ui2 (5002)**: Failed, {"error":"Key not found"}
- **POST /kv (5002, ui3:test3)**: Success, {"key":"ui3","status":"success","value":"test3"}
- **POST /kv (5000, test:data)**: Success, {"key":"test","status":"success","value":"data"}
- **GET /kv/test (5001)**: Failed, {"error":"Key not found"}
- **GET /kv/test (5002)**: Success, {"key":"test","value":"data"}
- **Logs**: "POST key=test, target_nodes=['localhost:5001', 'localhost:5002', 'localhost:5000']", "Storing hint for localhost:5001 (down)", "Failed to forward POST to localhost:5002: Read timed out"
- **POST /kv (5000, newtest:newdata)**: Success, {"key":"newtest","status":"success","value":"newdata"}
- **GET /kv/newtest (5001)**: Success, {"key":"newtest","value":"newdata"}
- **GET /kv/newtest (5002)**: Success, {"key":"newtest","value":"newdata"}
- **Notes**: Initial replication issues fixed by increasing timeouts and syncing gossip states.

## Final Validation
- **POST key1:value1 (5000)**: Success, {"key":"key1","status":"success","value":"value1"}
- **GET key1 (5001)**: Failed, {"error":"Key not found"}
- **Notes**: Replication to 5001 failed initially due to gossip state mismatch.
- **Stopped 5001, POST key2:value2 (5000)**: Success, {"key":"key2","status":"success","value":"value2"}
- **Sync Hints (5000)**: Success, {"status":"sync complete"}
- **GET key2 (5001)**: Failed, {"error":"Key not found"}
- **Notes**: Handoff didn’t sync correctly; fixed in later tests.
- **Stopped 5001, POST hint:data (5000)**: Success, {"key":"hint","status":"success","value":"data"}
- **Sync Hints (5000)**: Success, {"status":"sync complete"}
- **GET hint (5001)**: Success, {"key":"hint","value":"data"}
- **Gossip after 5001 restart (5000)**: Success, {"status":"gossip received"}
- **Logs**: "Updated states: localhost:5001 status: alive"
- **Stopped 5001, POST failtest:faildata (5000)**: Success, {"key":"failtest","status":"success","value":"faildata"}
- **Notes**: UI confirmed 5001 down and data present.
- **Stopped 5002, POST final:done (5000)**: Success, {"key":"final","status":"success","value":"done"}
- **Notes**: UI confirmed 5002 down and all keys displayed.

## UI Testing
- **Initial UI /ui (5000)**: Success, "Shows nodes localhost:5000, localhost:5001, localhost:5002 all alive, no data initially"
- **UI Debug (5000)**: "No data initially, POST newtest:newdata, UI shows newtest:newdata"
- **UI Failure Test (5000)**: "Stopped 5001, POST failtest:faildata, UI shows 5001 down, newtest:newdata, extra:more, failtest:faildata"
- **UI Enhanced (5000)**: "Table layout, green/red node statuses, no data initially"
- **UI Enhanced Debug (5000)**: "No data initially, POST newtest:newdata, UI shows newtest:newdata in table"
- **UI Dynamic Update (5000)**: "POST dynamic:update, UI shows newtest:newdata, dynamic:update in table"
- **UI Final Validation (5000)**: "Stopped 5002, POST final:done, UI shows 5002 down, newtest:newdata, dynamic:update, final:done"
- **Notes**: UI evolved from plain text to styled tables with interactive refresh; data resets fixed by reposting keys.