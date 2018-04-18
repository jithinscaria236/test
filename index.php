<form method="post" action="ep2.php" >
<table> <tr><td>EMPLOYEE ID </td><td><input type="text" name="t0"></td></tr>
<tr><td>EMPLOYEE NAME </td><td><input type="text" name="t1"></td></tr> <tr><td>DESIGNATION</td><td>
<input type="text" name="t2"></td></tr> <tr><td>DEDUCTION </td><td><input type="text" name="t3">
</td></tr> <tr><td>BASIC SALARY</td><td><input type="text" name="t4"></td></tr> <tr><td align="center">
<input type="SUBMIT" value="SUBMIT"></td></tr> </table> </form> <p align="center">
EMPLOYEE DETAILS</p>
 <table> <tr><td>EMPLOYEE NO</td><td>NAME</td><td>DESIGNATION</td> <td>HRA</td><td>DA</td><td>DEDUCTION </td>
 <td>BASIC SALARY</td><td>TOTAL SALARY </td></tr> <?php $con=mysql_connect("localhost","root","test");
mysql_select_db("a1");
$q=mysql_query("select *   from  employee"); while($a1=mysql_fetch_array($q)) { ?><tr><td><?php  echo $a1[0]; ?></td> <td> <?php  echo $a1[1]; ?></td> <td><?php  echo $a1[6]; ?></td> <td><?php  echo $a1[2]; ?></td> <td><?php  echo $a1[3]; ?></td> <td><?php  echo $a1[4]; ?></td> <td><?php echo $a1[5]; ?></td>


<td><?php echo $a1[7]; ?></td> </tr> <?php } ?> </table> </body> </html>
