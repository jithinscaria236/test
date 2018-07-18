# Readme
Using this script we can deploy a blueprint with single environment.
Options for the script file are given below
- -d,--download option uses for download blueprint from a git repo
- -e,--dstspcenvs option uses for  delete specific environment
- -E,--dstallenvs option uses for delete all environments
- -b,--dbp option uses for deploy a specific blueprint
- -B,--dallbp option uses for deploy all blueprints
- -D,--delbp option uses for delete blueprints
- -h,--help option uses for usage of the script
  
### How to run this script

Need to install jq.
```sh
$ yum  install jq
```
The script need python support for replacing input variables.

```sh
$ ./deploy.sh -b test.blueprint.reandeploy
$ ./deploy.sh -b test.blueprint.reandeploy -e 4520
```

