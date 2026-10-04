#!/usr/bin/env bash
set -euo pipefail

vpc=$1

for lb in $(aws elbv2 describe-load-balancers --query "LoadBalancers[?VpcId=='$vpc'].LoadBalancerArn" --output text); do
  aws elbv2 delete-load-balancer --load-balancer-arn "$lb"
  aws elbv2 wait load-balancers-deleted --load-balancer-arns "$lb"
done

for tg in $(aws elbv2 describe-target-groups --query "TargetGroups[?VpcId=='$vpc'].TargetGroupArn" --output text); do
  aws elbv2 delete-target-group --target-group-arn "$tg"
done

for eni in $(aws ec2 describe-network-interfaces --filters Name=vpc-id,Values="$vpc" Name=status,Values=available --query 'NetworkInterfaces[].NetworkInterfaceId' --output text); do
  aws ec2 delete-network-interface --network-interface-id "$eni"
done

sgs=$(aws ec2 describe-security-groups --filters Name=vpc-id,Values="$vpc" --query "SecurityGroups[?GroupName!='default'].GroupId" --output text)

for sg in $sgs; do
  ingress=$(aws ec2 describe-security-group-rules --filters Name=group-id,Values="$sg" --query 'SecurityGroupRules[?!IsEgress].SecurityGroupRuleId' --output text)
  egress=$(aws ec2 describe-security-group-rules --filters Name=group-id,Values="$sg" --query 'SecurityGroupRules[?IsEgress].SecurityGroupRuleId' --output text)
  if [ -n "$ingress" ]; then
    aws ec2 revoke-security-group-ingress --group-id "$sg" --security-group-rule-ids $ingress >/dev/null
  fi
  if [ -n "$egress" ]; then
    aws ec2 revoke-security-group-egress --group-id "$sg" --security-group-rule-ids $egress >/dev/null
  fi
done

for sg in $sgs; do
  aws ec2 delete-security-group --group-id "$sg"
done
